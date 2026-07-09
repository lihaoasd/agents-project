<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchRoles, startDebate } from '../../api/debateApi.js'

const router = useRouter()

// ── 数据 ──
const allDebaters = ref([])
const allJudges = ref([])
const loading = ref(true)
const starting = ref(false)
const error = ref('')

// ── 选择 ──
const question = ref('我们如何对待人工智能的发展？')
const selectedDebaters = ref([])
const selectedJudge = ref(null)
const crossRounds = ref(1)

// ── 搜索 / 折叠 ──
const search = ref('')
const openCategories = ref({})

const maxDebaters = 5

// ── 分类 ──
const categories = computed(() => {
  const map = {}
  for (const r of allDebaters.value) {
    const key = classifyCategory(r)
    if (!map[key]) map[key] = []
    map[key].push(r)
  }
  if (Object.keys(openCategories.value).length === 0) {
    const keys = Object.keys(map)
    if (keys.length) openCategories.value[keys[0]] = true
  }
  return Object.entries(map).map(([name, items]) => ({ name, items }))
})

const filteredCategories = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return categories.value
  return categories.value
    .map(c => ({
      ...c,
      items: c.items.filter(r =>
        r.name.toLowerCase().includes(q) ||
        (r.school || '').toLowerCase().includes(q) ||
        (r.persona_short || '').toLowerCase().includes(q) ||
        (r.period || '').toLowerCase().includes(q)
      ),
    }))
    .filter(c => c.items.length > 0)
})

const canStart = computed(() =>
  question.value.trim().length >= 3 &&
  selectedDebaters.value.length >= 2 &&
  selectedJudge.value &&
  !starting.value
)

function classifyCategory(role) {
  const m = {
    '儒家': '中国古典哲学（先秦）', '道家': '中国古典哲学（先秦）',
    '法家': '中国古典哲学（先秦）', '墨家': '中国古典哲学（先秦）',
    '兵家': '中国古典哲学（先秦）',
    '理学': '中国宋明理学', '心学': '中国宋明理学',
    '古希腊哲学': '西方古典哲学',
    '德国古典哲学': '西方近代哲学', '马克思主义': '西方近代哲学',
    '存在主义先驱': '西方近代哲学',
    '政治现实主义': '西方政治哲学', '社会契约论': '西方政治哲学',
    '自由主义': '西方政治哲学',
    '古典经济学': '经济学', '凯恩斯主义': '经济学', '奥地利学派': '经济学',
    '社会学': '社会科学', '心理学': '社会科学', '人类学': '社会科学',
    '语言学': '社会科学', '传播学': '社会科学', '政治学': '社会科学',
    '科学哲学': '现代哲学与科学', '政治哲学': '现代哲学与科学',
    '进化生物学': '现代哲学与科学',
    '集大成者': '学科全集大成者',
  }
  return m[role.school] || role.category || '其他'
}

function isSelected(id) { return selectedDebaters.value.some(d => d.id === id) }
function toggleDebater(role) {
  const idx = selectedDebaters.value.findIndex(d => d.id === role.id)
  if (idx >= 0) {
    selectedDebaters.value = selectedDebaters.value.filter(d => d.id !== role.id)
  } else if (selectedDebaters.value.length < maxDebaters) {
    selectedDebaters.value = [...selectedDebaters.value, role]
  }
}
function toggleCategory(name) { openCategories.value[name] = !openCategories.value[name] }

// ── 初始化 ──
onMounted(async () => {
  try {
    const data = await fetchRoles()
    allDebaters.value = data.debaters
    allJudges.value = data.judges
  } catch (e) {
    error.value = '无法连接后端服务，请确认后端已启动'
  } finally {
    loading.value = false
  }
})

// ── 开始辩论 ──
async function handleStart() {
  if (!canStart.value) return
  starting.value = true; error.value = ''
  try {
    const result = await startDebate({
      question: question.value.trim(),
      debater_ids: selectedDebaters.value.map(d => d.id),
      judge_id: selectedJudge.value.id,
      cross_examination_rounds: crossRounds.value,
    })
    if (result.session_id) {
      // 把参与者信息存到 sessionStorage，聊天室可以直接取
      sessionStorage.setItem(`debate_${result.session_id}`, JSON.stringify({
        question: result.question,
        debaters: result.debaters,
        judge: result.judge,
      }))
      router.push(`/debate/${result.session_id}`)
    }
  } catch (e) {
    error.value = e.message || '发起辩论失败'
    starting.value = false
  }
}
</script>

<template>
  <div class="debate-page">
    <!-- Hero -->
    <header class="debate-hero">
      <p style="margin:0 0 10px; color:var(--primary); font-size:13px; font-weight:700; letter-spacing:.12em; text-transform:uppercase;">Multi-Agent Debate</p>
      <h1>🎭 多Agent辩论</h1>
      <p class="desc">选择历史人物或思想家，围绕你的问题展开一场跨时空的辩论。每个辩者以自身学派立场发言，裁判最后统计并总结。</p>
    </header>

    <!-- 辩论问题 -->
    <section class="debate-panel">
      <div class="debate-section-title"><h2>辩论问题</h2></div>
      <textarea v-model="question" class="debate-textarea" placeholder="输入你的辩论问题，例如「人之初，性本善还是性本恶？」" rows="3" maxlength="500"></textarea>
      <div style="text-align:right; color:var(--muted); font-size:12px; margin-top:6px;">{{ question.length }}/500</div>
      <div class="debate-rounds">
        <label>质询轮次</label>
        <input type="number" v-model.number="crossRounds" min="1" max="3" />
        <span class="hint">（1-3 轮）</span>
      </div>
    </section>

    <!-- 选择辩者 -->
    <section class="debate-panel">
      <div class="debate-section-title">
        <h2>选择辩者</h2>
        <span class="count-badge">{{ selectedDebaters.length }} / {{ maxDebaters }}</span>
      </div>
      <div v-if="selectedDebaters.length" class="debate-chips">
        <span v-for="d in selectedDebaters" :key="d.id" class="debate-chip">{{ d.avatar }} {{ d.name }} <span class="chip-remove" @click="toggleDebater(d)">×</span></span>
      </div>
      <input v-model="search" class="debate-search" placeholder="🔍 搜索角色（姓名、学派…）" />
      <div v-if="loading" class="debate-loading"><span class="debate-spinner"></span>加载角色列表...</div>
      <template v-else>
        <div v-for="cat in filteredCategories" :key="cat.name" class="debate-category">
          <div class="debate-category-header" @click="toggleCategory(cat.name)">
            <span class="cat-arrow" :class="{ open: openCategories[cat.name] }">▶</span>
            <span>{{ cat.name }}</span>
            <span class="cat-count">{{ cat.items.length }}</span>
          </div>
          <div v-if="openCategories[cat.name]" class="debate-role-grid">
            <button
              v-for="role in cat.items" :key="role.id"
              class="debate-role-card"
              :class="{ selected: isSelected(role.id), disabled: !isSelected(role.id) && selectedDebaters.length >= maxDebaters }"
              :disabled="!isSelected(role.id) && selectedDebaters.length >= maxDebaters"
              type="button" @click="toggleDebater(role)"
            >
              <span class="role-avatar">{{ role.avatar }}</span>
              <div class="role-info">
                <div class="role-name">{{ role.name }}</div>
                <div class="role-school">{{ role.school }}<span v-if="role.period"> · {{ role.period }}</span></div>
                <div class="role-short">{{ role.persona_short }}</div>
              </div>
              <span class="role-check">{{ isSelected(role.id) ? '✓' : '+' }}</span>
            </button>
          </div>
        </div>
        <div v-if="filteredCategories.length === 0" style="text-align:center; color:var(--muted); padding:20px 0;">未匹配到角色</div>
      </template>
    </section>

    <!-- 选择裁判 -->
    <section class="debate-panel">
      <div class="debate-section-title">
        <h2>选择裁判</h2>
        <span class="count-badge">{{ selectedJudge ? 1 : 0 }} / 1</span>
      </div>
      <div v-if="loading" class="debate-loading"><span class="debate-spinner"></span>加载中...</div>
      <div v-else class="debate-role-grid">
        <button
          v-for="j in allJudges" :key="j.id"
          class="debate-role-card" :class="{ selected: selectedJudge?.id === j.id }"
          type="button" @click="selectedJudge = selectedJudge?.id === j.id ? null : j"
        >
          <span class="role-avatar">{{ j.avatar }}</span>
          <div class="role-info">
            <div class="role-name">{{ j.name }}</div>
            <div class="role-short">{{ j.persona_short }}</div>
          </div>
          <span class="role-check">{{ selectedJudge?.id === j.id ? '✓' : '+' }}</span>
        </button>
      </div>
    </section>

    <!-- 开始 -->
    <button class="debate-btn-start" :disabled="!canStart || starting" @click="handleStart">
      {{ starting ? '⏳ 辩论即将开始...' : '🎯 开始辩论' }}
    </button>
    <div v-if="error" class="debate-error-toast" @click="error = ''">{{ error }}</div>
  </div>
</template>
