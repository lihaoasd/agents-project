<script setup>
import { computed, ref } from 'vue'
import '../styles/travelJournal.css'

const props = defineProps({
  destination: { type: Object, required: true },
  spots: { type: Array, required: true },
  cultures: { type: Array, required: true },
  route: { type: Object, required: true },
  requirement: { type: String, default: '' },
})

const emit = defineEmits(['close'])

const journalRef = ref(null)
const exporting = ref(false)

const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const routeSegments = computed(() => {
  return props.route.segments || props.route.legs || []
})

const routeTotalDistance = computed(() => {
  const segs = routeSegments.value
  if (!segs.length) return props.route.totalDistance || ''
  const totalM = segs.reduce((sum, s) => sum + (Number(s.distanceMeters) || Number(s.distance) || 0), 0)
  if (totalM <= 0) return props.route.totalDistance || ''
  if (totalM < 1000) return `约 ${totalM} 米`
  return `约 ${(totalM / 1000).toFixed(1)} 公里`
})

const routeTotalDuration = computed(() => {
  const segs = routeSegments.value
  if (!segs.length) return props.route.totalDuration || ''
  const totalS = segs.reduce((sum, s) => sum + (Number(s.durationSeconds) || Number(s.duration) || 0), 0)
  if (totalS <= 0) return props.route.totalDuration || ''
  const h = Math.floor(totalS / 3600)
  const m = Math.floor((totalS % 3600) / 60)
  if (h && m) return `约 ${h} 小时 ${m} 分钟`
  if (h) return `约 ${h} 小时`
  return `约 ${m} 分钟`
})

function cultureForSpot(spot) {
  if (!props.cultures) return null
  return props.cultures.find((c) => c.spotId === spot.id) || null
}

function formatSegmentDistance(leg) {
  const meters = Number(leg.distanceMeters) || Number(leg.distance) || 0
  if (meters <= 0) return leg.distance || leg.distanceMeters || ''
  if (meters < 1000) return `约 ${meters} 米`
  return `约 ${(meters / 1000).toFixed(1)} 公里`
}

function formatSegmentDuration(leg) {
  const seconds = Number(leg.durationSeconds) || Number(leg.duration) || 0
  if (seconds <= 0) return leg.duration || leg.durationSeconds || ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h && m) return `约 ${h} 小时 ${m} 分钟`
  if (h) return `约 ${h} 小时`
  return `约 ${m} 分钟`
}

async function waitForImages(el) {
  const images = el.querySelectorAll('img')
  await Promise.allSettled(
    Array.from(images).map(
      (img) =>
        new Promise((resolve) => {
          if (img.complete) return resolve()
          img.addEventListener('load', resolve, { once: true })
          img.addEventListener('error', resolve, { once: true })
          setTimeout(resolve, 5000)
        }),
    ),
  )
}

async function downloadPdf() {
  const el = journalRef.value
  if (!el) return

  exporting.value = true

  try {
    await waitForImages(el)

    // Render content to canvas at 2x scale for sharp output
    const canvas = await html2canvas(el, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#faf7f2',
    })

    const imgData = canvas.toDataURL('image/jpeg', 0.92)
    const imgW = canvas.width   // pixels at 2x scale
    const imgH = canvas.height

    // Convert to mm: 1px at scale=2 = 0.5 real px at 96dpi → 1pt = 1/72in = 25.4/72 mm = 0.353mm
    // imgW px at 2x → imgW/2 real px at 96dpi → (imgW/2) * (25.4/96) mm
    const pdfW = (imgW / 2) * (25.4 / 96)
    const pdfH = (imgH / 2) * (25.4 / 96)

    // eslint-disable-next-line no-undef
    const { jsPDF } = window.jspdf
    const pdf = new jsPDF({
      orientation: pdfW > pdfH ? 'landscape' : 'portrait',
      unit: 'mm',
      format: [pdfW + 8, pdfH + 8], // 4mm margin on each side
    })

    pdf.addImage(imgData, 'JPEG', 4, 4, pdfW, pdfH)
    pdf.save(`旅行手帐_${props.destination.city}_${today.value}.pdf`)
  } finally {
    exporting.value = false
  }
}

function close() {
  emit('close')
}

defineExpose({ downloadPdf })
</script>

<template>
  <div class="journal-wrapper">
    <div class="journal-toolbar">
      <button class="journal-btn-download" :disabled="exporting" @click="downloadPdf">
        {{ exporting ? '正在生成 PDF…' : '下载 PDF' }}
      </button>
      <button class="journal-btn-close" @click="close">关闭预览</button>
    </div>

    <div ref="journalRef" class="journal-container">
      <!-- 封面 -->
      <section class="journal-cover">
        <h1 class="journal-title">旅行手帐</h1>
        <p class="journal-destination">{{ destination.province }} · {{ destination.city }}</p>
        <p class="journal-date">{{ today }}</p>
        <div class="journal-divider"></div>
        <p v-if="requirement" class="journal-requirement">"{{ requirement }}"</p>
      </section>

      <div class="journal-section-divider"></div>

      <!-- 目的地概述 -->
      <section class="journal-section">
        <h2 class="journal-section-title">目的地概述</h2>
        <p class="journal-section-subtitle">为你匹配的最佳文化旅行目的地</p>

        <div class="journal-dest-card">
          <div class="journal-dest-header">
            <span class="journal-dest-name">{{ destination.province }} · {{ destination.city }}</span>
            <span class="journal-dest-score">匹配度 {{ destination.matchScore }}%</span>
          </div>
          <p class="journal-dest-intro">{{ destination.intro }}</p>
          <div class="journal-tags">
            <span v-for="tag in destination.tags" :key="tag" class="journal-tag">{{ tag }}</span>
          </div>
        </div>
      </section>

      <div class="journal-section-divider"></div>

      <!-- 景点一览 -->
      <section class="journal-section">
        <h2 class="journal-section-title">景点一览</h2>
        <p class="journal-section-subtitle">共 {{ spots.length }} 个推荐景点</p>

        <article v-for="spot in spots" :key="spot.id" class="journal-spot-card">
          <div class="journal-spot-image-wrap">
            <img
              class="journal-spot-image"
              :src="spot.imageUrl || `https://picsum.photos/seed/cultural-${destination.id}-${spot.id}/640/420`"
              :alt="spot.imageAlt || spot.name"
              crossorigin="anonymous"
            />
          </div>
          <div class="journal-spot-body">
            <h3 class="journal-spot-name">{{ spot.name }}</h3>
            <div class="journal-spot-meta">
              <span>{{ spot.type }}</span>
              <span>{{ spot.visitTime }}</span>
            </div>
            <p class="journal-spot-reason">{{ spot.recommendReason }}</p>
            <div class="journal-spot-info">
              <div class="journal-spot-info-item">
                <span class="journal-spot-info-label">地址</span>
                <span>{{ spot.address }}</span>
              </div>
              <div class="journal-spot-info-item">
                <span class="journal-spot-info-label">开放</span>
                <span>{{ spot.openingHours }}</span>
              </div>
              <div class="journal-spot-info-item">
                <span class="journal-spot-info-label">门票</span>
                <span>{{ spot.ticket }}</span>
              </div>
            </div>
            <div class="journal-tags" style="margin-top: 10px;">
              <span v-for="tag in spot.cultureTags" :key="tag" class="journal-tag">{{ tag }}</span>
            </div>
          </div>
        </article>
      </section>

      <div class="journal-section-divider"></div>

      <!-- 文化解读 -->
      <section class="journal-section">
        <h2 class="journal-section-title">文化解读</h2>
        <p class="journal-section-subtitle">每个景点的历史文化、风俗、地理与美食提示</p>

        <article v-for="spot in spots" :key="'culture-' + spot.id" class="journal-culture-card">
          <h3 class="journal-culture-spot-name">{{ spot.name }}</h3>

          <template v-if="cultureForSpot(spot)">
            <p class="journal-culture-overview">{{ cultureForSpot(spot).overview }}</p>

            <div v-if="cultureForSpot(spot).historyCulture" class="journal-culture-block">
              <p class="journal-culture-block-title">历史文化</p>
              <p class="journal-culture-block-text">{{ cultureForSpot(spot).historyCulture }}</p>
            </div>

            <div v-if="cultureForSpot(spot).customs" class="journal-culture-block">
              <p class="journal-culture-block-title">风俗习惯</p>
              <p class="journal-culture-block-text">{{ cultureForSpot(spot).customs }}</p>
            </div>

            <div v-if="cultureForSpot(spot).geography" class="journal-culture-block">
              <p class="journal-culture-block-title">地理特点</p>
              <p class="journal-culture-block-text">{{ cultureForSpot(spot).geography }}</p>
            </div>

            <div v-if="cultureForSpot(spot).foodSuggestion" class="journal-culture-block">
              <p class="journal-culture-block-title">美食提示</p>
              <p class="journal-culture-block-text">{{ cultureForSpot(spot).foodSuggestion }}</p>
            </div>
          </template>

          <p v-else class="journal-culture-overview" style="color: #8b7355;">
            暂无该景点的文化解读数据。
          </p>
        </article>
      </section>

      <div class="journal-section-divider"></div>

      <!-- 路线规划 -->
      <section class="journal-section">
        <h2 class="journal-section-title">路线规划</h2>
        <p class="journal-section-subtitle">{{ route.mode ? `出行方式：${route.mode}` : '' }}</p>

        <div class="journal-route-summary">
          <div class="journal-route-stat">
            <p class="journal-route-stat-label">总距离</p>
            <p class="journal-route-stat-value">{{ routeTotalDistance }}</p>
          </div>
          <div class="journal-route-stat">
            <p class="journal-route-stat-label">预计用时</p>
            <p class="journal-route-stat-value">{{ routeTotalDuration }}</p>
          </div>
        </div>

        <p v-if="route.description" class="journal-route-desc">{{ route.description }}</p>
        <p v-if="route.fallback" class="journal-route-fallback">当前为备用路线</p>

        <p v-if="route.orderedSpots && route.orderedSpots.length" class="journal-route-spots-title">
          游览顺序
        </p>
        <div v-if="route.orderedSpots && route.orderedSpots.length" class="journal-route-spots">
          <div v-for="(spot, idx) in route.orderedSpots" :key="spot.name" class="journal-route-spot-badge">
            <span class="journal-route-spot-index">{{ idx + 1 }}</span>
            <span>{{ spot.name || spot }}</span>
          </div>
        </div>

        <p v-if="routeSegments.length" class="journal-route-legs-title">路线分段详情</p>
        <article v-for="(leg, idx) in routeSegments" :key="leg.from + leg.to + idx" class="journal-route-leg">
          <div class="journal-route-leg-index">{{ idx + 1 }}</div>
          <div class="journal-route-leg-content">
            <p class="journal-route-leg-path">{{ leg.from }} → {{ leg.to }}</p>
            <p class="journal-route-leg-stats">{{ formatSegmentDistance(leg) }} · {{ formatSegmentDuration(leg) }}</p>
            <p v-if="leg.detail || leg.tip" class="journal-route-leg-tip">{{ leg.detail || leg.tip }}</p>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>