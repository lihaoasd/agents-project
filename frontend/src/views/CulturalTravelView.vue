<script setup>
import { computed, ref } from 'vue'
import '../styles/culturalTravel.css'
import AmapRouteMap from '../components/AmapRouteMap.vue'
import { planRoute, recommendCulturalInterpretations, recommendPlaces, recommendScenicSpots } from '../api/tripPlanApi'
import {
  getCultureByDestination,
  getResourcesByDestination,
  getSpotsByDestination,
  progressSteps,
} from '../data/staticTravelData'

const requirement = ref('')
const recommendedCities = ref([])
const selectedDestination = ref(null)
const generatedSpots = ref([])
const selectedSpot = ref(null)
const generatedCultures = ref([])
const generatedRoute = ref(null)
const generatedResources = ref(null)
const routeMode = ref('auto')
const routePace = ref('balanced')
const routeOrigin = ref('')
const routeDestination = ref('')
const routePlanning = ref(false)
const routeError = ref('')
const resourceTab = ref('books')
const notice = ref('')
const loadingStep = ref(null)

const currentStep = computed(() => {
  if (generatedResources.value) return 'resources'
  if (generatedRoute.value) return 'route'
  if (generatedCultures.value.length) return 'culture'
  if (generatedSpots.value.length) return 'spots'
  if (selectedDestination.value) return 'city'
  return recommendedCities.value.length ? 'city' : ''
})

const selectedCulture = computed(() => {
  if (!selectedSpot.value) return generatedCultures.value[0] || null
  return generatedCultures.value.find((culture) => culture.spotId === selectedSpot.value.id) || null
})

const cultureSections = computed(() => {
  if (!selectedCulture.value) return []
  return [
    { title: '历史文化', text: selectedCulture.value.historyCulture || selectedCulture.value.history || '' },
    { title: '风俗习惯', text: selectedCulture.value.customs || '' },
    { title: '地理特点', text: selectedCulture.value.geography || '' },
    { title: '美食提示', text: selectedCulture.value.foodSuggestion || '' },
  ].filter((section) => section.text)
})

const routeMapPoints = computed(() => {
  const orderedSpots = generatedRoute.value?.orderedSpots || []
  const points = orderedSpots
    .map((spot, index) => ({
      name: spot.name,
      index,
      lng: Number(spot.lng),
      lat: Number(spot.lat),
    }))
    .filter((point) => Number.isFinite(point.lng) && Number.isFinite(point.lat))

  if (!points.length) {
    return orderedSpots.map((spot, index) => ({
      name: spot.name,
      index,
      x: 18 + index * 18,
      y: 68 - index * 14,
    }))
  }

  const lngValues = points.map((point) => point.lng)
  const latValues = points.map((point) => point.lat)
  const minLng = Math.min(...lngValues)
  const maxLng = Math.max(...lngValues)
  const minLat = Math.min(...latValues)
  const maxLat = Math.max(...latValues)
  const lngSpan = maxLng - minLng || 1
  const latSpan = maxLat - minLat || 1

  return points.map((point) => ({
    ...point,
    x: 12 + ((point.lng - minLng) / lngSpan) * 76,
    y: 16 + (1 - (point.lat - minLat) / latSpan) * 68,
  }))
})

const mapLinePoints = computed(() => {
  return routeMapPoints.value.map((point) => `${point.x},${point.y}`).join(' ')
})

// ---------- 路线总计 —— 从 segments 累加 distanceMeters / durationSeconds，不依赖 LLM 输出 ----------

const routeTotalDistance = computed(() => {
  const segs = generatedRoute.value?.segments || generatedRoute.value?.legs || []
  if (!segs.length) return generatedRoute.value?.totalDistance || ''
  const totalM = segs.reduce((sum, s) => sum + (Number(s.distanceMeters) || Number(s.distance) || 0), 0)
  if (totalM <= 0) return generatedRoute.value?.totalDistance || ''
  if (totalM < 1000) return `约 ${totalM} 米`
  return `约 ${(totalM / 1000).toFixed(1)} 公里`
})

const routeTotalDuration = computed(() => {
  const segs = generatedRoute.value?.segments || generatedRoute.value?.legs || []
  if (!segs.length) return generatedRoute.value?.totalDuration || ''
  const totalS = segs.reduce((sum, s) => sum + (Number(s.durationSeconds) || Number(s.duration) || 0), 0)
  if (totalS <= 0) return generatedRoute.value?.totalDuration || ''
  const h = Math.floor(totalS / 3600)
  const m = Math.floor((totalS % 3600) / 60)
  if (h && m) return `约 ${h} 小时 ${m} 分钟`
  if (h) return `约 ${h} 小时`
  return `约 ${m} 分钟`
})

// 单段距离格式化
function formatSegmentDistance(leg) {
  const meters = Number(leg.distanceMeters) || Number(leg.distance) || 0
  if (meters <= 0) return leg.distance || leg.distanceMeters || ''
  if (meters < 1000) return `约 ${meters} 米`
  return `约 ${(meters / 1000).toFixed(1)} 公里`
}

// 单段耗时格式化
function formatSegmentDuration(leg) {
  const seconds = Number(leg.durationSeconds) || Number(leg.duration) || 0
  if (seconds <= 0) return leg.duration || leg.durationSeconds || ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h && m) return `约 ${h} 小时 ${m} 分钟`
  if (h) return `约 ${h} 小时`
  return `约 ${m} 分钟`
}

// -----------------------------------------------------------------------------------------------

async function recommendCities() {
  resetAfterCity()
  const text = requirement.value.trim()
  if (!text) {
    notice.value = '请输入文化旅行需求'
    return
  }
  loadingStep.value = 'city'
  try {
    const result = await recommendPlaces(text)
    recommendedCities.value = result.data.destinations
    notice.value = result.data.notice || ''
  } catch (err) {
    notice.value = err.message || '网络错误，无法连接后端服务'
  } finally {
    loadingStep.value = null
  }
}

function resetAfterCity() {
  notice.value = ''
  loadingStep.value = null
  selectedDestination.value = null
  selectedSpot.value = null
  generatedSpots.value = []
  generatedCultures.value = []
  generatedResources.value = null
  routeMode.value = 'auto'
  routePace.value = 'balanced'
  routeOrigin.value = ''
  routeDestination.value = ''
  routePlanning.value = false
  routeError.value = ''
}

function selectDestination(destination) {
  selectedDestination.value = destination
  loadingStep.value = null
  selectedSpot.value = null
  generatedSpots.value = []
  generatedCultures.value = []
  generatedRoute.value = null
  generatedResources.value = null
  notice.value = '已完成“地方推荐”节点。请选择“生成旅游景点”继续。'
}

async function generateSpots() {
  if (!selectedDestination.value) return
  generatedSpots.value = []
  selectedSpot.value = null
  generatedCultures.value = []
  generatedRoute.value = null
  generatedResources.value = null
  routePlanning.value = false
  routeError.value = ''
  loadingStep.value = 'spots'
  try {
    const result = await recommendScenicSpots({
      requirement: requirement.value.trim(),
      destinationId: selectedDestination.value.id,
      destinationCity: selectedDestination.value.city,
      destinationProvince: selectedDestination.value.province,
    })
    generatedSpots.value = result.data.spots
    selectedSpot.value = generatedSpots.value[0] || null
    generatedCultures.value = []
    generatedRoute.value = null
    generatedResources.value = null
    notice.value = result.data.notice || `已根据 ${selectedDestination.value.city} 生成 ${generatedSpots.value.length} 个文化旅行景点。`
  } catch (err) {
    generatedSpots.value = getSpotsByDestination(selectedDestination.value.id)
    selectedSpot.value = generatedSpots.value[0] || null
    notice.value = `生成景点失败，已使用静态数据。共 ${generatedSpots.value.length} 个景点。`
  } finally {
    loadingStep.value = null
  }
}

function selectSpot(spot) {
  selectedSpot.value = spot
}

async function generateCultureIntros() {
  if (!generatedSpots.value.length || !selectedDestination.value) return
  loadingStep.value = 'culture'
  generatedCultures.value = []
  generatedResources.value = null
  routePlanning.value = false
  routeError.value = ''
  try {
    const result = await recommendCulturalInterpretations({
      requirement: requirement.value.trim(),
      destinationId: selectedDestination.value.id,
      destinationCity: selectedDestination.value.city,
      destinationProvince: selectedDestination.value.province,
      spots: generatedSpots.value,
    })
    generatedCultures.value = result.data.cultures
    notice.value = result.data.notice || `已生成 ${generatedCultures.value.length} 个景点的综合文化解读。`
  } catch (err) {
    generatedCultures.value = generatedSpots.value.map((spot) => getCultureByDestination(selectedDestination.value.id, spot))
    notice.value = `生成综合文化解读失败，已使用静态数据。共 ${generatedCultures.value.length} 个景点。`
  } finally {
    selectedSpot.value = generatedSpots.value[0] || null
    loadingStep.value = null
  }
}

async function generateRoutePlan() {
  if (!selectedDestination.value || !generatedSpots.value.length) return
  routePlanning.value = true
  routeError.value = ''
  generatedResources.value = null
  try {
    const result = await planRoute({
      requirement: requirement.value.trim(),
      destinationId: selectedDestination.value.id,
      destinationCity: selectedDestination.value.city,
      destinationProvince: selectedDestination.value.province,
      spots: generatedSpots.value,
      mode: routeMode.value,
      origin: routeOrigin.value ? { name: routeOrigin.value } : undefined,
      destination: routeDestination.value ? { name: routeDestination.value } : undefined,
      constraints: {
        pace: routePace.value,
        preferTransit: routeMode.value === 'transit',
        avoidLongWalk: routePace.value === 'relaxed',
      },
    })
    generatedRoute.value = result.data
    notice.value = result.data.fallback
      ? '高德路线暂时不可用，已使用备用路线。'
      : `已根据 ${selectedDestination.value.city} 生成真实地图路线规划。`
  } catch (err) {
    routeError.value = err.message || '路线规划失败'
    notice.value = routeError.value
  } finally {
    routePlanning.value = false
  }
}

function generateResources() {
  if (!selectedDestination.value) return
  generatedResources.value = getResourcesByDestination(selectedDestination.value.id)
  resourceTab.value = 'books'
  notice.value = '已生成相关书籍、短视频和文章推荐。'
}

function resourceItems(type) {
  if (!generatedResources.value) return []
  return generatedResources.value[type] || []
}

function resourceLabel(type) {
  return {
    books: '书籍',
    videos: '短视频',
    articles: '文章',
  }[type] || '推荐'
}

function markerStyle(point) {
  return {
    left: `${point.x}%`,
    top: `${point.y}%`,
  }
}

function pinStyle(index) {
  const positions = [
    { left: '18%', top: '68%' },
    { left: '48%', top: '44%' },
    { left: '76%', top: '24%' },
  ]
  return positions[index] || { left: '50%', top: '50%' }
}

function stepClass(stepKey) {
  if (!currentStep.value) return 'pending'
  const currentIndex = progressSteps.findIndex((step) => step.key === currentStep.value)
  const stepIndex = progressSteps.findIndex((step) => step.key === stepKey)
  if (stepIndex < currentIndex) return 'done'
  if (stepIndex === currentIndex) return 'active'
  return 'pending'
}

function placeholderClass(stepKey) {
  if (!currentStep.value) return stepKey === 'city' ? 'active' : 'pending'
  const currentIndex = progressSteps.findIndex((step) => step.key === currentStep.value)
  const stepIndex = progressSteps.findIndex((step) => step.key === stepKey)
  if (stepIndex <= currentIndex) return 'active'
  return 'pending'
}
</script>

<template>
  <main class="page">
    <header class="hero">
      <div>
        <p class="eyebrow">文化旅行 Agent · 静态原型</p>
        <h1>输入旅行需求，生成地方、景点与综合文化解读</h1>
        <p class="hero-desc">
          项目包含 5 个进度节点：地方推荐、旅游景点生成、综合文化解读、地图路线规划、推荐相关书籍/短视频/文章。
          当前已实现全部五个节点：需求输入、地市推荐、景点生成、景点综合文化解读、地图路线规划和内容资源推荐。
        </p>
      </div>
    </header>

    <section class="panel input-panel">
      <label for="requirement">你的文化旅行需求</label>
      <textarea
        id="requirement"
        v-model="requirement"
        rows="5"
        placeholder="例如：想带孩子了解唐代文化，3天，预算中等，希望有博物馆和美食体验"
      />
      <div class="actions">
        <button
          class="primary"
          type="button"
          :disabled="loadingStep === 'city'"
          @click="recommendCities"
        >
          <span v-if="loadingStep === 'city'" class="spinner"></span>
          {{ loadingStep === 'city' ? '正在分析需求，推荐地方…' : '推荐地方' }}
        </button>
        <button class="secondary" type="button" @click="requirement = '想带孩子了解唐代文化，3天，预算中等'">
          填入示例
        </button>
      </div>
      <p v-if="!recommendedCities.length && loadingStep !== 'city'" class="hint">
        输入文化旅行需求，点击"推荐地方"将通过 AI 生成地方推荐。
      </p>
      <p v-if="loadingStep === 'city'" class="loading">
        <span class="spinner"></span>
        正在调用大模型分析用户需求，推荐合适地市，请稍候...
      </p>
    </section>

    <section v-if="recommendedCities.length" class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Progress 01 / 05</p>
          <h2>地方推荐</h2>
        </div>
        <span class="status">{{ selectedDestination ? '已完成' : '进行中' }}</span>
      </div>

      <ol class="progress-steps">
        <li
          v-for="step in progressSteps"
          :key="step.key"
          class="progress-step"
          :class="stepClass(step.key)"
        >
          <span class="step-dot">{{ progressSteps.indexOf(step) + 1 }}</span>
          <span>{{ step.label }}</span>
        </li>
      </ol>

      <p class="section-desc">为你推荐了 <strong>{{ recommendedCities.length }}</strong> 个文化旅行目的地，可左右滑动浏览</p>

      <div class="destination-grid">
        <button
          v-for="destination in recommendedCities"
          :key="destination.id"
          class="destination-card"
          :class="{ selected: selectedDestination?.id === destination.id }"
          type="button"
          @click="selectDestination(destination)"
        >
          <div class="destination-top">
            <div>
              <strong>{{ destination.province }} · {{ destination.city }}</strong>
              <span>匹配度 {{ destination.matchScore }}%</span>
            </div>
            <span class="score">{{ destination.matchScore }}</span>
          </div>
          <div class="tags">
            <span v-for="tag in destination.tags" :key="tag">{{ tag }}</span>
          </div>
          <div class="destination-reasons">
            <div v-for="reason in destination.reasons" :key="reason" class="destination-reason">
              <span class="reason-dot"></span>
              <span>{{ reason }}</span>
            </div>
          </div>
        </button>
      </div>
    </section>

    <section v-if="selectedDestination" class="panel selected-panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Selected Destination</p>
          <h2>已选择：{{ selectedDestination.province }} · {{ selectedDestination.city }}</h2>
        </div>
      </div>

      <p class="destination-intro">{{ selectedDestination.intro }}</p>

      <div class="tags">
        <span v-for="tag in selectedDestination.tags" :key="tag">{{ tag }}</span>
      </div>

      <div class="actions">
        <button
          class="primary"
          type="button"
          :disabled="loadingStep === 'spots'"
          @click="generateSpots"
        >
          <span v-if="loadingStep === 'spots'" class="spinner"></span>
          {{ loadingStep === 'spots' ? '正在分析需求，推荐景点…' : generatedSpots.length ? '重新生成旅游景点' : '生成旅游景点' }}
        </button>
      </div>

      <p v-if="notice" class="notice">{{ notice }}</p>
    </section>

    <section v-if="generatedSpots.length" class="panel spots-panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Progress 02 / 05</p>
          <h2>旅游景点生成</h2>
        </div>
        <span class="status">已完成</span>
      </div>

      <p class="section-desc">为你推荐了 <strong>{{ generatedSpots.length }}</strong> 个文化旅行景点，可左右滑动浏览</p>

      <p v-if="loadingStep === 'spots'" class="loading">
        <span class="spinner"></span>
        正在调用大模型分析用户需求和目的地，推荐合适景点，请稍候...
      </p>

      <div class="spot-grid">
        <article
          v-for="spot in generatedSpots"
          :key="spot.id"
          class="spot-card"
          :class="{ selected: selectedSpot?.id === spot.id }"
          @click="selectSpot(spot)"
        >
          <img
            class="spot-image"
            :src="spot.imageUrl || `https://picsum.photos/seed/cultural-${selectedDestination?.id || 'none'}-${spot.id}/640/420`"
            :alt="spot.imageAlt || spot.name"
            loading="lazy"
          />
          <div class="spot-body">
            <div class="spot-meta">
              <span>{{ spot.type }}</span>
              <span>{{ spot.visitTime }}</span>
            </div>
            <h3>{{ spot.name }}</h3>
            <p>{{ spot.recommendReason }}</p>
            <dl>
              <div>
                <dt>地址</dt>
                <dd>{{ spot.address }}</dd>
              </div>
              <div>
                <dt>开放时间</dt>
                <dd>{{ spot.openingHours }}</dd>
              </div>
              <div>
                <dt>门票</dt>
                <dd>{{ spot.ticket }}</dd>
              </div>
            </dl>
            <div class="tags compact">
              <span v-for="tag in spot.cultureTags" :key="tag">{{ tag }}</span>
            </div>
          </div>
        </article>
      </div>

      <div class="route-controls">
        <label>
          出行方式
          <select v-model="routeMode">
            <option value="auto">自动</option>
            <option value="driving">自驾</option>
            <option value="transit">公共交通</option>
          </select>
        </label>
        <label>
          游玩节奏
          <select v-model="routePace">
            <option value="relaxed">轻松</option>
            <option value="balanced">均衡</option>
            <option value="intensive">紧凑</option>
          </select>
        </label>
        <label>
          起点
          <input v-model="routeOrigin" placeholder="例如：北京南站，留空则使用城市中心" />
        </label>
        <label>
          终点
          <input v-model="routeDestination" placeholder="例如：首都机场，留空则返回城市中心" />
        </label>
      </div>

      <div class="actions culture-actions">
        <button
          class="primary"
          type="button"
          :disabled="loadingStep === 'culture'"
          @click="generateCultureIntros"
        >
          <span v-if="loadingStep === 'culture'" class="spinner"></span>
          {{ loadingStep === 'culture' ? '正在生成综合文化解读…' : generatedCultures.length ? '重新生成综合文化解读' : '生成综合文化解读' }}
        </button>
        <button class="secondary" type="button" :disabled="routePlanning" @click="generateRoutePlan">
          <span v-if="routePlanning" class="spinner"></span>
          {{ routePlanning ? '正在调用高德规划路线…' : generatedRoute ? '重新生成地图路线规划' : '生成地图路线规划' }}
        </button>
      </div>
    </section>

    <section v-if="generatedCultures.length" class="panel culture-panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Progress 03 / 05</p>
          <h2>综合文化解读</h2>
        </div>
        <span class="status">已完成</span>
      </div>

      <div class="culture-layout">
        <aside class="culture-list">
          <button
            v-for="culture in generatedCultures"
            :key="culture.spotId"
            class="culture-item"
            :class="{ active: selectedSpot?.id === culture.spotId }"
            type="button"
            @click="selectSpot(generatedSpots.find((spot) => spot.id === culture.spotId))"
          >
            <strong>{{ culture.spotName || culture.name }}</strong>
            <span>查看综合文化</span>
          </button>
        </aside>

        <article class="culture-detail">
          <p class="eyebrow">Culture Detail</p>
          <h3>{{ selectedSpot?.name || selectedCulture?.spotName || selectedCulture?.name || generatedCultures[0].spotName }}</h3>
          <p v-if="selectedCulture?.overview" class="culture-overview">{{ selectedCulture.overview }}</p>
          <div v-if="cultureSections.length" class="culture-sections">
            <section v-for="section in cultureSections" :key="section.title" class="culture-section">
              <h4>{{ section.title }}</h4>
              <p>{{ section.text }}</p>
            </section>
          </div>
        </article>
      </div>
    </section>

    <section v-if="generatedRoute" class="panel route-panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Progress 04 / 05</p>
          <h2>地图路线规划</h2>
        </div>
        <span class="status">已完成</span>
      </div>

      <p class="section-desc">
        已根据推荐目的地、景点位置和你的行程要求生成路线。高德服务不可用时会自动使用备用路线。
      </p>

      <div class="route-layout">
        <AmapRouteMap
          :ordered-spots="generatedRoute.orderedSpots"
          :segments="generatedRoute.segments || generatedRoute.legs || []"
          :origin="generatedRoute.origin || null"
          :destination="generatedRoute.destinationPoint || generatedRoute.origin || null"
          :mode="generatedRoute.mode || 'auto'"
          :nav-url="generatedRoute.navUrl || ''"
          :total-distance="routeTotalDistance"
          :total-duration="routeTotalDuration"
        />

        <aside class="route-summary">
          <div class="summary-card">
            <span>总距离</span>
            <strong>{{ routeTotalDistance }}</strong>
          </div>
          <div class="summary-card">
            <span>预计用时</span>
            <strong>{{ routeTotalDuration }}</strong>
          </div>
          <p>{{ generatedRoute.description || generatedRoute.notices?.[0] }}</p>
          <p v-if="generatedRoute.fallback" class="warning">当前为备用路线</p>
        </aside>
      </div>

      <div class="route-steps">
        <article v-for="(leg, index) in (generatedRoute.segments || generatedRoute.legs || [])" :key="leg.from + leg.to + index" class="route-step">
          <div class="route-step-index">{{ index + 1 }}</div>
          <div>
            <h3>{{ leg.from }} → {{ leg.to }}</h3>
            <p>{{ formatSegmentDistance(leg) }} · {{ formatSegmentDuration(leg) }}</p>
            <span>{{ leg.detail || leg.tip }}</span>
          </div>
        </article>
      </div>

      <div class="actions culture-actions">
        <button class="primary" type="button" @click="generateResources">
          {{ generatedResources ? '重新生成推荐内容' : '推荐相关书籍/短视频/文章' }}
        </button>
      </div>
    </section>

    <section v-if="generatedResources" class="panel resources-panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Progress 05 / 05</p>
          <h2>推荐相关书籍、短视频、文章</h2>
        </div>
        <span class="status">已完成</span>
      </div>

      <p class="section-desc">
        以下为根据 {{ selectedDestination.city }} 推荐的文化旅行延伸阅读和观看内容，当前使用静态数据展示。
      </p>

      <div class="resource-tabs">
        <button
          v-for="type in ['books', 'videos', 'articles']"
          :key="type"
          class="resource-tab"
          :class="{ active: resourceTab === type }"
          type="button"
          @click="resourceTab = type"
        >
          {{ resourceLabel(type) }}
        </button>
      </div>

      <div class="resource-grid">
        <article v-for="item in resourceItems(resourceTab)" :key="item.title" class="resource-card">
          <span class="resource-type">{{ resourceLabel(resourceTab) }}</span>
          <h3>{{ item.title }}</h3>
          <p v-if="item.author">作者：{{ item.author }}</p>
          <p v-if="item.source">来源：{{ item.source }}</p>
          <p>{{ item.reason }}</p>
        </article>
      </div>
    </section>

    <section class="panel future-panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Next Steps</p>
          <h2>后续节点规划</h2>
        </div>
      </div>

      <div class="future-grid">
        <div
          v-for="step in progressSteps"
          :key="step.key"
          class="future-card"
          :class="placeholderClass(step.key)"
        >
          <strong>{{ step.label }}</strong>
          <p>
            <template v-if="step.key === 'city'">
              已实现需求输入、静态地市推荐和用户选择。
            </template>
            <template v-else-if="step.key === 'spots'">
              已实现根据已选地市生成静态景点列表。
            </template>
            <template v-else-if="step.key === 'culture'">
              已实现景点历史、风俗、地理等综合文化解读和景点切换查看。
            </template>
            <template v-else-if="step.key === 'route'">
              已实现基于推荐目的地、景点位置和高德 API 的路线规划。
            </template>
            <template v-else-if="step.key === 'resources'">
              已实现相关书籍、短视频和文章推荐。
            </template>
            <template v-else>
              后续基于已选地市和景点生成对应内容。
            </template>
          </p>
        </div>
      </div>
    </section>
  </main>
</template>
