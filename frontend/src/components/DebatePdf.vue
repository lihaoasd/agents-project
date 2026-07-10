<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import '../styles/debatePdf.css'

const props = defineProps({
  sessionData: { type: Object, required: true },
})

const emit = defineEmits(['close'])

const pdfRef = ref(null)
const exporting = ref(false)

/* ── 日期 ── */
const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

/* ── 基础数据 ── */
const question = computed(() => props.sessionData.question || '')
const createdDisplay = computed(() => {
  const t = props.sessionData.created_at || ''
  return t ? t.slice(0, 19).replace('T', ' ') : ''
})
const completedDisplay = computed(() => {
  const t = props.sessionData.completed_at || ''
  return t ? t.slice(0, 19).replace('T', ' ') : ''
})
const duration = computed(() => {
  const d = props.sessionData.duration_seconds
  if (!d) return ''
  const m = Math.floor(d / 60)
  const s = Math.floor(d % 60)
  return m ? `${m} 分 ${s} 秒` : `${s} 秒`
})
const debaters = computed(() => props.sessionData?.config?.debaters || [])
const judge = computed(() => props.sessionData?.config?.judge || {})
const stages = computed(() => props.sessionData?.stages || {})

/* ── 辩者名映射 ── */
const nameMap = computed(() => {
  const map = {}
  for (const d of debaters.value) {
    map[d.id] = d.name
  }
  return map
})

/* ── 学派的 CSS class ── */
function schoolClass(school) {
  const map = {
    '儒家': 'confucian',
    '道家': 'daoist',
    '法家': 'legalist',
    '墨家': 'mohist',
    '心学': 'mind',
    '理学': 'confucian',
    '兵家': 'military',
    '社会学': 'military',
    '心理学': 'confucian',
    '人类学': 'military',
    '语言学': 'mohist',
    '传播学': 'mind',
    '政治学': 'legalist',
  }
  const cls = map[school] || 'confucian'
  return `dpdf-school-${cls}`
}

/* ── 查找学派 ── */
function findSchool(speakerId) {
  for (const d of debaters.value) {
    if (d.id === speakerId) return d.school || ''
  }
  return ''
}

/* ── 最高票数 ── */
const maxVotes = computed(() => {
  const tally = stages.value.voting?.tally || {}
  const values = Object.values(tally).map(Number).filter(v => v > 0)
  return values.length ? Math.max(...values) : 0
})

/* ── 投票人列表 ── */
function votersFor(debaterId) {
  const votes = stages.value.voting?.votes || []
  return votes
    .filter(v => v.vote_for === debaterId || v.voted_for_id === debaterId)
    .map(v => {
      const vid = v.voter || v.voter_id
      return nameMap.value[vid] || vid
    })
}

/* ── 渲染 Markdown ── */
function renderMd(text) {
  if (!text) return ''
  try { return marked.parse(text) } catch { return text.replace(/\n/g, '<br>') }
}

/* ── 获取消息中的说话者信息 ── */
function speakerInfo(speaker) {
  if (!speaker) return { avatar: '🎭', name: '', id: '' }
  return {
    avatar: speaker.avatar || '🎭',
    name: speaker.name || '',
    id: speaker.id || '',
  }
}

/* ── 等待图片加载 ── */
async function waitForImages(el) {
  const images = el.querySelectorAll('img')
  await Promise.allSettled(
    Array.from(images).map(
      img => new Promise(resolve => {
        if (img.complete) return resolve()
        img.addEventListener('load', resolve, { once: true })
        img.addEventListener('error', resolve, { once: true })
        setTimeout(resolve, 5000)
      }),
    ),
  )
}

/* ── 下载 PDF（html2canvas 截图 + jsPDF） ── */
async function downloadPdf() {
  const el = pdfRef.value
  if (!el) return

  exporting.value = true
  try {
    await waitForImages(el)

    const canvas = await html2canvas(el, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#f8f9fa',
    })

    const imgData = canvas.toDataURL('image/jpeg', 0.92)
    const imgW = canvas.width
    const imgH = canvas.height

    const pdfW = (imgW / 2) * (25.4 / 96)
    const pdfH = (imgH / 2) * (25.4 / 96)

    const { jsPDF } = window.jspdf
    const pdf = new jsPDF({
      orientation: pdfW > pdfH ? 'landscape' : 'portrait',
      unit: 'mm',
      format: [pdfW + 8, pdfH + 8],
    })

    pdf.addImage(imgData, 'JPEG', 4, 4, pdfW, pdfH)
    pdf.save(`辩论记录_${props.sessionData.session_id.slice(0, 8)}_${today.value}.pdf`)
  } finally {
    exporting.value = false
  }
}

function close() {
  emit('close')
}
</script>

<template>
  <div class="dpdf-wrapper">
    <div class="dpdf-toolbar">
      <button class="dpdf-btn-download" :disabled="exporting" @click="downloadPdf">
        {{ exporting ? '正在生成 PDF…' : '📄 下载 PDF' }}
      </button>
      <button class="dpdf-btn-close" @click="close">关闭预览</button>
    </div>

    <div ref="pdfRef" class="dpdf-container">
      <!-- ====== 封面 ====== -->
      <section class="dpdf-cover">
        <h1 class="dpdf-cover-title">多Agent辩论</h1>
        <div class="dpdf-cover-question">{{ question }}</div>
        <div class="dpdf-cover-meta">
          <div>辩论ID：{{ sessionData.session_id }}</div>
          <div>辩论时间：{{ createdDisplay }}</div>
          <div v-if="completedDisplay">完成时间：{{ completedDisplay }}</div>
          <div v-if="duration">耗时：{{ duration }}</div>
          <div>辩者：<strong v-for="(d, i) in debaters" :key="d.id">{{ i ? '、' : '' }}{{ d.name }}{{ d.school ? '（' + d.school + '）' : '' }}</strong></div>
          <div>裁判：<strong>{{ judge.name || '' }}</strong></div>
        </div>
        <div class="dpdf-cover-divider"></div>
      </section>

      <hr class="dpdf-section-divider">

      <!-- ====== 立论陈词 ====== -->
      <section v-if="stages.opening?.messages?.length">
        <h2 class="dpdf-phase-title">📜 立论</h2>
        <div
          v-for="msg in stages.opening.messages"
          :key="msg.id"
          class="dpdf-message"
          :class="schoolClass(findSchool(msg.speaker?.id || ''))"
        >
          <div class="dpdf-message-speaker">
            {{ speakerInfo(msg.speaker).avatar }}
            {{ speakerInfo(msg.speaker).name }}
            <span class="dpdf-message-school">· {{ findSchool(msg.speaker?.id || '') }}</span>
          </div>
          <div v-if="msg.target?.id && msg.target.id !== 'all'" class="dpdf-message-target">
            → @{{ msg.target.name }}
          </div>
          <div class="dpdf-message-content" v-html="renderMd(msg.content)"></div>
        </div>
      </section>

      <hr v-if="stages.opening?.messages?.length" class="dpdf-section-divider">

      <!-- ====== 质询 ====== -->
      <section v-if="stages.cross_examine?.qa_pairs?.length">
        <h2 class="dpdf-phase-title">⚔️ 质询</h2>
        <p class="dpdf-phase-subtitle">共 {{ stages.cross_examine.rounds || 1 }} 轮</p>

        <div v-for="(qa, idx) in stages.cross_examine.qa_pairs" :key="'qa-' + idx" class="dpdf-qa-pair">
          <div class="dpdf-qa-round-label">第 {{ qa.round }} 轮：{{ qa.asker?.name || '' }} → @{{ qa.answerer?.name || '' }}</div>

          <div class="dpdf-qa-question">
            <div class="dpdf-qa-speaker">
              <span class="dpdf-qa-label dpdf-qa-label-ask">问</span>
              {{ qa.asker?.name || '' }}<span class="dpdf-qa-school"> · {{ findSchool(qa.asker?.id || '') }}</span>
            </div>
            <div class="dpdf-qa-content">{{ qa.question }}</div>
          </div>

          <div class="dpdf-qa-answer">
            <div class="dpdf-qa-speaker">
              <span class="dpdf-qa-label dpdf-qa-label-ans">答</span>
              {{ qa.answerer?.name || '' }}<span class="dpdf-qa-school"> · {{ findSchool(qa.answerer?.id || '') }}</span>
            </div>
            <div class="dpdf-qa-content">{{ qa.answer }}</div>
          </div>
        </div>
      </section>

      <hr v-if="stages.cross_examine?.qa_pairs?.length" class="dpdf-section-divider">

      <!-- ====== 结辩 ====== -->
      <section v-if="stages.closing?.messages?.length">
        <h2 class="dpdf-phase-title">🏁 结辩</h2>
        <div
          v-for="msg in stages.closing.messages"
          :key="msg.id"
          class="dpdf-message"
          :class="schoolClass(findSchool(msg.speaker?.id || ''))"
        >
          <div class="dpdf-message-speaker">
            {{ speakerInfo(msg.speaker).avatar }}
            {{ speakerInfo(msg.speaker).name }}
            <span class="dpdf-message-school">· {{ findSchool(msg.speaker?.id || '') }}</span>
          </div>
          <div class="dpdf-message-content" v-html="renderMd(msg.content)"></div>
        </div>
      </section>

      <hr v-if="stages.closing?.messages?.length" class="dpdf-section-divider">

      <!-- ====== 投票 ====== -->
      <section v-if="stages.voting?.votes?.length">
        <h2 class="dpdf-phase-title">🗳️ 投票</h2>

        <table class="dpdf-vote-table">
          <thead>
            <tr><th>辩者</th><th>得票</th><th>投票者</th></tr>
          </thead>
          <tbody>
            <tr
              v-for="(count, debaterId) in stages.voting.tally"
              :key="debaterId"
              :class="{ 'dpdf-winner-row': parseInt(count) === maxVotes }"
            >
              <td>{{ nameMap[debaterId] || debaterId }}</td>
              <td>{{ count }} 票</td>
              <td>
                {{ votersFor(debaterId).join('、') || '—' }}
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="stages.voting.awards" class="dpdf-awards">
          <span v-if="stages.voting.awards.best_argument" class="dpdf-award-badge dpdf-award-best-argument">
            🏆 最佳论点：{{ typeof stages.voting.awards.best_argument === 'string' ? stages.voting.awards.best_argument : stages.voting.awards.best_argument.recipient }}
          </span>
          <span v-if="stages.voting.awards.best_cross_examine" class="dpdf-award-badge dpdf-award-best-cross">
            🎯 最佳质询：{{ typeof stages.voting.awards.best_cross_examine === 'string' ? stages.voting.awards.best_cross_examine : stages.voting.awards.best_cross_examine.recipient }}
          </span>
        </div>
      </section>

      <hr v-if="stages.voting?.votes?.length" class="dpdf-section-divider">

      <!-- ====== 裁判总结 ====== -->
      <section v-if="stages.judge_summary?.content">
        <h2 class="dpdf-phase-title">📝 裁判总结</h2>
        <div class="dpdf-judge-card">
          <div class="dpdf-judge-content" v-html="renderMd(stages.judge_summary.content)"></div>
        </div>
      </section>
    </div>
  </div>
</template>
