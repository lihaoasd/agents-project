<script setup>
import { computed, ref } from 'vue'
import '../styles/culturalTravel.css'
import {
  getRecommendedDestinations,
  getResourcesByDestination,
  getRouteByDestination,
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
const resourceTab = ref('books')
const notice = ref('')

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

const selectedCultureText = computed(() => {
  if (!selectedCulture.value) return ''
  return [
    selectedCulture.value.overview,
    selectedCulture.value.history,
    selectedCulture.value.value,
    selectedCulture.value.tip,
  ].join('')
})

function recommendCities() {
  resetAfterCity()
  recommendedCities.value = getRecommendedDestinations(requirement.value.trim())
}

function resetAfterCity() {
  notice.value = ''
  selectedDestination.value = null
  selectedSpot.value = null
  generatedSpots.value = []
  generatedCultures.value = []
  generatedRoute.value = null
  generatedResources.value = null
}

function selectDestination(destination) {
  selectedDestination.value = destination
  selectedSpot.value = null
  generatedSpots.value = []
  generatedCultures.value = []
  generatedRoute.value = null
  generatedResources.value = null
  notice.value = '已完成“地方推荐”节点。请选择“生成旅游景点”继续。'
}

function generateSpots() {
  if (!selectedDestination.value) return
  generatedSpots.value = getSpotsByDestination(selectedDestination.value.id)
  selectedSpot.value = generatedSpots.value[0] || null
  generatedCultures.value = []
  generatedRoute.value = null
  generatedResources.value = null
  notice.value = `已根据 ${selectedDestination.value.city} 生成 ${generatedSpots.value.length} 个文化旅行景点。`
}

function selectSpot(spot) {
  selectedSpot.value = spot
}

function generateCultureIntros() {
  if (!generatedSpots.value.length) return
  generatedCultures.value = generatedSpots.value
    .filter((spot) => spot.culture)
    .map((spot) => ({
      spotId: spot.id,
      name: spot.name,
      ...spot.culture,
    }))
  selectedSpot.value = generatedSpots.value[0] || null
  generatedRoute.value = null
  generatedResources.value = null
  notice.value = `已生成 ${generatedCultures.value.length} 个景点的历史文化介绍。`
}

function generateRoutePlan() {
  if (!selectedDestination.value) return
  generatedRoute.value = getRouteByDestination(selectedDestination.value.id)
  generatedResources.value = null
  notice.value = '已生成基于高德地图思路的静态路线规划。真实地图路线可在后续接入高德 API Key。'
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
        <h1>输入旅行需求，生成地方、景点与历史文化</h1>
        <p class="hero-desc">
          项目包含 5 个进度节点：地方推荐、旅游景点生成、历史文化介绍、地图路线规划、推荐相关书籍/短视频/文章。
          当前已实现全部五个节点：需求输入、地市推荐、景点生成、景点历史文化介绍、地图路线规划和内容资源推荐。
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
        <button class="primary" type="button" @click="recommendCities">
          推荐地方
        </button>
        <button class="secondary" type="button" @click="requirement = '想带孩子了解唐代文化，3天，预算中等'">
          填入示例
        </button>
      </div>
      <p v-if="!recommendedCities.length" class="hint">
        当前使用静态数据，不调用后端 API。
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
          <ul>
            <li v-for="reason in destination.reasons" :key="reason">{{ reason }}</li>
          </ul>
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
        <button class="primary" type="button" @click="generateSpots">
          {{ generatedSpots.length ? '重新生成旅游景点' : '生成旅游景点' }}
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

      <p class="section-desc">
        以下为根据 {{ selectedDestination.city }} 生成的文化旅行景点，当前使用静态数据展示。
      </p>

      <div class="spot-grid">
        <article
          v-for="spot in generatedSpots"
          :key="spot.id"
          class="spot-card"
          :class="{ selected: selectedSpot?.id === spot.id }"
          @click="selectSpot(spot)"
        >
          <img class="spot-image" :src="spot.imageUrl" :alt="spot.imageAlt" loading="lazy" />
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

      <div class="actions culture-actions">
        <button class="primary" type="button" @click="generateCultureIntros">
          {{ generatedCultures.length ? '重新生成历史文化介绍' : '生成历史文化介绍' }}
        </button>
        <button class="secondary" type="button" @click="generateRoutePlan">
          {{ generatedRoute ? '重新生成地图路线规划' : '生成地图路线规划' }}
        </button>
      </div>
    </section>

    <section v-if="generatedCultures.length" class="panel culture-panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Progress 03 / 05</p>
          <h2>历史文化介绍</h2>
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
            <strong>{{ culture.name }}</strong>
            <span>查看历史文化</span>
          </button>
        </aside>

        <article class="culture-detail">
          <p class="eyebrow">Culture Detail</p>
          <h3>{{ selectedSpot?.name || generatedCultures[0].name }}</h3>
          <div class="culture-text">{{ selectedCultureText }}</div>
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
        当前使用静态路线数据模拟高德地图规划结果。后续接入高德 API Key 后，可生成真实驾车、步行或公交路线。
      </p>

      <div class="route-layout">
        <div class="map-placeholder">
          <div class="map-header">
            <strong>{{ generatedRoute.provider }}</strong>
            <a :href="generatedRoute.navUrl" target="_blank" rel="noreferrer">打开高德地图</a>
          </div>
          <div class="map-canvas">
            <div v-for="(spot, index) in generatedSpots" :key="spot.id" class="map-pin" :style="pinStyle(index)">
              <span>{{ index + 1 }}</span>
            </div>
            <div class="map-route-line" />
          </div>
        </div>

        <aside class="route-summary">
          <div class="summary-card">
            <span>总距离</span>
            <strong>{{ generatedRoute.totalDistance }}</strong>
          </div>
          <div class="summary-card">
            <span>预计用时</span>
            <strong>{{ generatedRoute.totalDuration }}</strong>
          </div>
          <p>{{ generatedRoute.description }}</p>
        </aside>
      </div>

      <div class="route-steps">
        <article v-for="(leg, index) in generatedRoute.legs" :key="leg.from + leg.to" class="route-step">
          <div class="route-step-index">{{ index + 1 }}</div>
          <div>
            <h3>{{ leg.from }} → {{ leg.to }}</h3>
            <p>{{ leg.distance }} · {{ leg.duration }}</p>
            <span>{{ leg.tip }}</span>
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
              已实现景点历史文化介绍和景点切换查看。
            </template>
            <template v-else-if="step.key === 'route'">
              已实现基于静态数据的高德地图路线规划展示。
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
