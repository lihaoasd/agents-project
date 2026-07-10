<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchSession, getExportUrl } from '../../api/debateApi.js'
import { marked } from 'marked'
import DebatePdf from '../../components/DebatePdf.vue'

const props = defineProps({ sessionId: { type: String, required: true } })

const session = ref(null)
const loading = ref(true)
const showPdf = ref(false)

onMounted(async () => {
  try {
    const data = await fetchSession(props.sessionId)
    // 后端直接返回 { data: {...} } 或不包裹
    session.value = data?.data || data
  } catch (e) {
    console.error('加载辩论结果失败:', e)
  } finally {
    loading.value = false
  }
})

/* ── 参与者映射 ── */
const debaterById = computed(() => {
  const map = {}
  for (const d of (session.value?.config?.debaters || session.value?.debaters || [])) {
    map[d.id] = d
  }
  return map
})

/* ── 胜者 ── */
const winner = computed(() => {
  // 从 judge_result 中取
  const jr = session.value?.judge_result
  if (jr?.winner_name) return { name: jr.winner_name, votes: 0 }
  // 从 stages.judge_tally 中取
  const tally = session.value?.stages?.judge_tally
  if (tally?.winner) return tally.winner
  return null
})

/* ── 票数排行 ── */
const tallyRows = computed(() => {
  const votes = session.value?.judge_result?.votes || session.value?.stages?.voting?.votes || []
  if (!votes.length) return []
  const count = {}
  for (const v of votes) {
    const vid = v.voted_for_id || v.vote_for
    if (!vid) continue
    count[vid] = (count[vid] || 0) + 1
  }
  return Object.entries(count)
    .map(([id, c]) => {
      const d = debaterById.value[id] || {}
      const voters = votes
        .filter(v => (v.voted_for_id || v.vote_for) === id)
        .map(v => {
          const voterId = v.voter_id || v.voter
          return debaterById.value[voterId]?.name || voterId
        })
      return { id, name: d.name || id, avatar: d.avatar || '🎭', votes: c, voters }
    })
    .sort((a, b) => b.votes - a.votes)
})

/* ── 获奖 ── */
const awards = computed(() => session.value?.stages?.judge_tally?.awards)

/* ── 裁判总结 ── */
const summaryContent = computed(() => {
  const jr = session.value?.judge_result
  if (jr?.summary) return jr.summary
  // 从 stages 中取
  const s = session.value?.stages?.judge_summary
  return s?.content || s?.messages?.[0]?.content || ''
})

const question = computed(() => session.value?.config?.question || session.value?.question || '')
const debaters = computed(() => session.value?.config?.debaters || session.value?.debaters || [])
const judge = computed(() => session.value?.config?.judge || session.value?.judge || {})
const duration = computed(() => {
  const d = session.value?.duration_seconds
  if (!d) return ''
  const m = Math.floor(d / 60); const s = Math.floor(d % 60)
  return m ? `${m} 分 ${s} 秒` : `${s} 秒`
})

function renderMd(text) {
  if (!text) return ''
  try { return marked.parse(text) } catch { return text.replace(/\n/g, '<br>') }
}

function exportFormat(format) {
  if (format === 'pdf') {
    showPdf.value = true
  } else {
    window.open(getExportUrl(props.sessionId, format))
  }
}
</script>

<template>
  <div class="debate-page">
    <header class="debate-hero">
      <p style="margin:0 0 10px; color:var(--primary); font-size:13px; font-weight:700; letter-spacing:.12em; text-transform:uppercase;">Debate Result</p>
      <h1>🏆 辩论结果</h1>
      <p class="desc">{{ question }}</p>
    </header>

    <div v-if="loading" class="debate-panel" style="text-align:center; padding:60px 28px;">
      <div class="debate-loading" style="justify-content:center;">
        <span class="debate-spinner"></span>加载辩论记录...
      </div>
    </div>

    <template v-else-if="session">
      <div v-if="winner" class="debate-result-winner">
        <div class="trophy">🏆</div>
        <div class="name">{{ winner.name }}</div>
        <div class="votes">{{ winner.votes ? `获得 ${winner.votes} 票胜出` : '胜出' }}</div>
      </div>

      <section v-if="tallyRows.length" class="debate-panel">
        <div class="debate-section-title">
          <h2>🗳️ 投票结果</h2>
          <span class="count-badge">{{ tallyRows.length }} 人</span>
        </div>
        <table class="debate-vote-table">
          <thead>
            <tr><th>辩者</th><th>票数</th><th>投票人</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in tallyRows" :key="row.id" :class="{ 'winner-row': row.name === winner?.name }">
              <td>{{ row.avatar }} {{ row.name }}</td>
              <td>{{ row.votes }}</td>
              <td>{{ row.voters.join(', ') || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="awards" class="debate-awards">
          <span v-if="awards.best_argument" class="debate-award best-argument">
            🏆 最佳论点：{{ typeof awards.best_argument === 'string' ? awards.best_argument : awards.best_argument.recipient }}
          </span>
          <span v-if="awards.best_cross_examine" class="debate-award best-cross">
            🎯 最佳质询：{{ typeof awards.best_cross_examine === 'string' ? awards.best_cross_examine : awards.best_cross_examine.recipient }}
          </span>
        </div>
      </section>

      <section v-if="summaryContent" class="debate-panel">
        <div class="debate-section-title"><h2>📝 裁判总结</h2></div>
        <div class="debate-summary" v-html="renderMd(summaryContent)"></div>
      </section>

      <section class="debate-panel">
        <div class="debate-section-title"><h2>辩论信息</h2></div>
        <p style="color:var(--muted); line-height:1.8; margin:0;">
          辩者：<strong v-for="(d, i) in debaters" :key="d.id">{{ i ? '、' : '' }}{{ d.name }}</strong><br />
          裁判：<strong>{{ judge.name || '' }}</strong>
          <span v-if="duration"> · 耗时：<strong>{{ duration }}</strong></span>
          <span v-if="session.total_messages"> · 消息数：<strong>{{ session.total_messages }}</strong></span>
        </p>
        <div class="debate-actions" style="margin-top:20px; justify-content:center;">
          <button class="debate-btn-secondary" @click="exportFormat('pdf')">📄 导出 PDF</button>
          <button class="debate-btn-secondary" @click="exportFormat('md')">📝 导出 Markdown</button>
          <button class="debate-btn-secondary" @click="exportFormat('json')">📋 导出 JSON</button>
        </div>
      </section>

      <div style="text-align:center;">
        <button class="debate-btn-start" @click="$router.push('/debate')">🎯 开始新一轮辩论</button>
      </div>
    </template>

    <div v-else class="debate-panel" style="text-align:center; padding:60px 28px; color:var(--muted);">
      辩论记录不存在或已过期
    </div>

    <!-- 前端 PDF 导出 -->
    <DebatePdf v-if="showPdf && session" :sessionData="session" @close="showPdf = false" />
  </div>
</template>
