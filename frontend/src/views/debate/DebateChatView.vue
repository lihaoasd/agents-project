<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getStreamUrl } from '../../api/debateApi.js'
import { marked } from 'marked'

const props = defineProps({ sessionId: { type: String, required: true } })

/* ── 参与者信息（从 sessionStorage 读取） ── */
const sessionMeta = ref({ question: '', debaters: [], judge: null })
const debaterMap = reactive({})  // id → {name, avatar, school}
const judgeInfo = ref(null)

onMounted(() => {
  try {
    const raw = sessionStorage.getItem(`debate_${props.sessionId}`)
    if (raw) {
      const meta = JSON.parse(raw)
      sessionMeta.value = meta
      for (const d of meta.debaters || []) {
        debaterMap[d.id] = { name: d.name, avatar: d.avatar || '🎭', school: d.school || '', role: 'debater' }
      }
      if (meta.judge) {
        judgeInfo.value = { name: meta.judge.name, avatar: meta.judge.avatar || '⚖️', school: '', role: 'judge' }
        debaterMap[meta.judge.id] = judgeInfo.value
      }
    }
  } catch {}
})

/* ── 状态 ── */
const speakingIds = reactive(new Set())
const errorMsg = ref('')
const statusText = ref('辩论进行中...')
const showScrollBtn = ref(false)
const msgContainer = ref(null)

// 消息存储
const bubbleMap = reactive(new Map())
const messageList = computed(() => [...bubbleMap.values()])

// 追踪活跃消息 key（speaker_end 缺少字段时回退查找）
const lastKeyBySpeaker = {}  // speaker_id → key

let eventSource = null
let retryCount = 0
let lastMsgId = ''  // 断线重连用
const MAX_RETRY = 3

/* ── 工具 ── */
function msgKey(speakerId, phase, targetId, round) {
  return `${speakerId}_${phase}_${targetId || 'all'}_r${round || 0}`
}

function speakerInfo(id, name) {
  // 优先用 sessionStorage 的详细数据，回退用 SSE 里的 name
  const m = debaterMap[id]
  return {
    id,
    name: m?.name || name || id,
    avatar: m?.avatar || '🎭',
    school: m?.school || '',
    role: m?.role || 'debater',
  }
}

const PHASE_LABELS = {
  opening: '📜 立论陈词',
  cross_examination: '⚔️ 交叉质询',
  closing: '🏁 结辩陈词',
  voting: '🗳️ 投票',
  judge_tally: '📊 裁判统计',
  judge_summary: '📝 裁判总结',
}

/* ── SSE ── */
onMounted(() => connectSSE())
onUnmounted(() => closeSSE())

function connectSSE() {
  closeSSE()
  let url = getStreamUrl(props.sessionId)
  if (lastMsgId) url += `?resume_from=${encodeURIComponent(lastMsgId)}`
  eventSource = new EventSource(url)

  eventSource.addEventListener('open', () => {
    retryCount = 0
    errorMsg.value = ''
  })

  // ── status（重连回放提示）──
  eventSource.addEventListener('status', (e) => {
    const data = JSON.parse(e.data)
    if (data.replay) {
      statusText.value = '🔄 正在恢复之前的消息...'
    }
  })

  // ── message_replay（重连补发消息）──
  eventSource.addEventListener('message_replay', (e) => {
    const data = JSON.parse(e.data)
    lastMsgId = data.msg_id || lastMsgId
    const speaker = speakerInfo(data.speaker_id, data.speaker_name)
    const target = data.target_id && data.target_id !== 'all'
      ? speakerInfo(data.target_id, data.target_name)
      : { id: 'all', name: '所有人' }
    const key = `replay_${data.msg_id}`
    if (bubbleMap.has(key)) return  // 避免重复
    bubbleMap.set(key, {
      id: key, type: 'msg',
      speaker, target,
      content: data.full_content || '',
      done: true,
      school: speaker.school,
    })
  })

  // ── phase_start ──
  eventSource.addEventListener('phase_start', (e) => {
    const data = JSON.parse(e.data)
    const phase = data.phase
    speakingIds.clear()
    const label = data.label || PHASE_LABELS[phase] || phase
    const roundText = data.round ? ` · 第${data.round}轮` : ''
    bubbleMap.set(`phase_${phase}_${data.round || 0}`, {
      id: `phase_${phase}_${data.round || 0}`, type: 'phase', phase, label: label + roundText,
    })
    lastMsgId = `phase_${phase}_${data.round || 0}`  // 重连检查点
    statusText.value = label
    scrollToBottom()
  })

  // ── speaker_start ──
  eventSource.addEventListener('speaker_start', (e) => {
    const data = JSON.parse(e.data)
    const speaker = speakerInfo(data.speaker_id, data.speaker_name)
    const target = data.target_id
      ? speakerInfo(data.target_id, data.target_name)
      : { id: 'all', name: '所有人' }
    const key = msgKey(data.speaker_id, data.phase, data.target_id, data.round)
    lastKeyBySpeaker[data.speaker_id] = key  // 记录活跃 key，speaker_end 回退用

    bubbleMap.set(key, {
      id: key, type: 'msg',
      speaker, target, content: '', done: false,
      school: speaker.school,
    })
    speakingIds.add(data.speaker_id)
    statusText.value = `${speaker.name} 正在发言...`
    scrollToBottom()
  })

  // ── message_delta ── （后端用 "token" 字段）
  eventSource.addEventListener('message_delta', (e) => {
    const data = JSON.parse(e.data)
    let key = msgKey(data.speaker_id, data.phase, data.target_id, data.round)
    if (!bubbleMap.has(key)) {
      key = lastKeyBySpeaker[data.speaker_id] || key
    }
    const entry = bubbleMap.get(key)
    if (entry && entry.type === 'msg') {
      entry.content += (data.token || '')
      bubbleMap.set(key, { ...entry })
    }
  })

  // ── speaker_end ──（后端仅传 speaker_id + phase，可能缺 target_id / round）
  eventSource.addEventListener('speaker_end', (e) => {
    const data = JSON.parse(e.data)
    // 优先用精确 key，回退到 lastKeyBySpeaker
    let key = msgKey(data.speaker_id, data.phase, data.target_id, data.round)
    if (!bubbleMap.has(key)) {
      key = lastKeyBySpeaker[data.speaker_id] || key
    }
    const entry = bubbleMap.get(key)
    if (entry && entry.type === 'msg') {
      entry.done = true
      speakingIds.delete(data.speaker_id)
      bubbleMap.set(key, { ...entry })
    }
    scrollToBottom()
  })

  // ── vote_start ──（显示投票开始提示）
  eventSource.addEventListener('vote_start', (e) => {
    const data = JSON.parse(e.data)
    statusText.value = `${data.voter_name} 正在投票...`
  })

  // ── vote_complete ──（投票结果作为一条消息显示）
  eventSource.addEventListener('vote_complete', (e) => {
    const data = JSON.parse(e.data)
    const voter = speakerInfo(data.voter_id, data.voter_name)
    const voted = speakerInfo(data.voted_for_id, data.voted_for_name)
    const key = `vote_${data.voter_id}`
    bubbleMap.set(key, {
      id: key, type: 'msg',
      speaker: voter,
      target: { id: 'all', name: '所有人' },
      content: `🗳️ 投票给 **${voted.name}**\n\n> ${data.reason || ''}`,
      done: true,
      school: '',
    })
    scrollToBottom()
  })

  // ── judge_tally_start ──
  eventSource.addEventListener('judge_tally_start', () => {
    statusText.value = '裁判正在统计票数...'
  })

  // ── judge_tally_complete ──
  eventSource.addEventListener('judge_tally_complete', (e) => {
    const data = JSON.parse(e.data)
    const judge = judgeInfo.value || { id: 'judge', name: '裁判', avatar: '⚖️', school: '', role: 'judge' }
    const key = 'judge_tally_result'
    bubbleMap.set(key, {
      id: key, type: 'msg',
      speaker: judge,
      target: { id: 'all', name: '所有人' },
      content: `🏆 获胜者：**${data.winner_name}**`,
      done: true,
      school: '',
    })
    scrollToBottom()
  })

  // ── done ──
  eventSource.addEventListener('done', (e) => {
    const data = JSON.parse(e.data)
    if (data.replay) return  // 跳过重连回放里的 done
    bubbleMap.set('done_banner', {
      id: 'done_banner', type: 'done',
      winnerName: data.winner_name || '',
      winnerVotes: 0,
    })
    statusText.value = '辩论已结束'
    closeSSE()
    scrollToBottom()
  })

  // ── error ──
  eventSource.addEventListener('error', (e) => {
    try {
      const data = JSON.parse(e.data)
      errorMsg.value = data.message || '辩论中出现错误'
    } catch {
      // EventSource 原生错误事件（连接断开），交给 onerror 处理
    }
  })

  // ── 连接断开 ──
  eventSource.onerror = () => {
    if (eventSource?.readyState === EventSource.CLOSED) {
      closeSSE()
      if (retryCount < MAX_RETRY) {
        retryCount++
        errorMsg.value = `连接断开，正在重连 (${retryCount}/${MAX_RETRY})...`
        setTimeout(() => connectSSE(), 2000 * retryCount)
      } else {
        errorMsg.value = '连接失败，请刷新页面重试'
        statusText.value = '连接失败'
      }
    }
  }
}

function closeSSE() {
  if (eventSource) { eventSource.close(); eventSource = null }
}

function scrollToBottom() {
  nextTick(() => {
    const el = msgContainer.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function onScroll() {
  const el = msgContainer.value
  if (!el) return
  showScrollBtn.value = el.scrollHeight - el.scrollTop - el.clientHeight > 100
}

function exportFormat(format) {
  window.open(`http://127.0.0.1:8000/api/debate/sessions/${props.sessionId}/export?format=${format}`)
}

function renderMd(text) {
  if (!text) return ''
  try { return marked.parse(text) } catch { return text.replace(/\n/g, '<br>') }
}
</script>

<template>
  <div class="debate-page">
    <!-- 顶栏 -->
    <div class="debate-chat-topbar">
      <button class="back-btn" @click="$router.push('/debate')">←</button>
      <div class="title">{{ sessionMeta.question || '多Agent辩论' }}</div>
      <div class="participants">
        <div v-for="d in sessionMeta.debaters" :key="d.id" class="p-dot" :title="d.name">
          {{ d.avatar }} <span class="status-ring" :class="speakingIds.has(d.id) ? 'active' : 'idle'"></span>
        </div>
        <div v-if="sessionMeta.judge" class="p-dot" :title="sessionMeta.judge.name">
          {{ sessionMeta.judge.avatar }} <span class="status-ring idle"></span>
        </div>
      </div>
    </div>

    <!-- 聊天面板 -->
    <div class="debate-chat-panel">
      <div ref="msgContainer" class="debate-messages" @scroll="onScroll">
        <template v-for="item in messageList" :key="item.id">
          <!-- 阶段横幅 -->
          <div v-if="item.type === 'phase'" class="debate-phase-banner">{{ item.label }}</div>

          <!-- 消息气泡 -->
          <div v-else-if="item.type === 'msg'" class="debate-bubble-wrapper" :class="item.speaker?.role || 'debater'">
            <div class="debate-bubble-header">
              <span class="avatar">{{ item.speaker?.avatar }}</span>
              <span class="name">{{ item.speaker?.name }}</span>
              <span v-if="item.school" class="school">· {{ item.school }}</span>
              <span v-if="item.target?.id !== 'all'" class="at-target">
                → <strong>@{{ item.target?.name }}</strong>
              </span>
            </div>
            <div
              class="debate-bubble"
              :class="[
                item.speaker?.role === 'judge' ? 'debate-bubble-judge' : '',
                item.school ? 'school-' + item.school : '',
              ]"
            >
              <div v-if="item.done" v-html="renderMd(item.content)"></div>
              <div v-else>
                <span :class="item.content ? 'typing-cursor' : 'typing-indicator'">
                  {{ item.content || '正在输入...' }}
                </span>
              </div>
            </div>
          </div>

          <!-- 结束横幅 -->
          <div v-else-if="item.type === 'done'" class="debate-done-banner">
            <div class="trophy">🏆</div>
            <div class="winner-name">{{ item.winnerName }}</div>
            <div class="votes-text">辩论结束</div>
            <div class="debate-actions" style="justify-content:center;">
              <button class="debate-btn-primary" @click="$router.push(`/debate/${sessionId}/result`)">查看完整总结</button>
              <button class="debate-btn-secondary" @click="exportFormat('md')">📝 导出 MD</button>
              <button class="debate-btn-secondary" @click="exportFormat('json')">📋 导出 JSON</button>
            </div>
          </div>
        </template>

        <div v-if="messageList.length === 0" class="debate-empty">
          <div class="icon">⏳</div>
          <div>连接辩论中...</div>
        </div>
      </div>

      <div class="debate-chat-bottombar">
        <button v-if="showScrollBtn" class="scroll-btn" @click="scrollToBottom">跳至底部 ▼</button>
        <span v-else-if="statusText" class="status-text">{{ statusText }}</span>
        <span v-else class="status-text">&nbsp;</span>
      </div>
    </div>

    <div v-if="errorMsg" class="debate-error-toast" @click="errorMsg = ''">{{ errorMsg }}</div>
  </div>
</template>
