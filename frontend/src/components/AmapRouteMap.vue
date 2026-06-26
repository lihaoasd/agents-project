<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  orderedSpots: { type: Array, default: () => [] },
  segments: { type: Array, default: () => [] },
  origin: { type: Object, default: null },
  destination: { type: Object, default: null },
  mode: { type: String, default: 'transit' },
  navUrl: { type: String, default: '' },
  totalDistance: { type: String, default: '' },
  totalDuration: { type: String, default: '' },
})

const container = ref(null)
const ready = ref(false)
const loadError = ref('')

let mapInstance = null
let markers = []
let polylines = []

function waitForAMap() {
  return new Promise((resolve, reject) => {
    if (typeof AMap !== 'undefined') return resolve()
    const max = 60
    let count = 0
    const timer = setInterval(() => {
      count++
      if (typeof AMap !== 'undefined') {
        clearInterval(timer)
        resolve()
      }
      if (count >= max) {
        clearInterval(timer)
        reject(new Error('高德地图 SDK 加载超时'))
      }
    }, 500)
  })
}

onMounted(async () => {
  if (!container.value) return
  try {
    await waitForAMap()
  } catch (err) {
    loadError.value = err.message
    return
  }
  nextTick(() => {
    buildMap()
  })
})

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.destroy()
    mapInstance = null
  }
})

watch(
  () => [props.orderedSpots, props.segments, props.origin],
  () => {
    if (ready.value) redraw()
  },
  { deep: true }
)

function buildMap() {
  const center = firstValidCoordinate()
  mapInstance = new AMap.Map(container.value, {
    zoom: 12,
    center,
    resizeEnable: true,
  })
  ready.value = true
  redraw()
}

function redraw() {
  clearOverlays()
  const spots = validSpots()
  if (!spots.length) return

  drawMarkers(spots)
  const path = buildPolylinePath(spots)
  if (path.length > 1) drawPolyline(path)
  mapInstance.setFitView(null, false, [60, 60, 60, 60])
}

function clearOverlays() {
  markers.forEach((m) => {
    if (m.setMap) m.setMap(null)
  })
  markers = []
  polylines.forEach((p) => {
    if (p.setMap) p.setMap(null)
  })
  polylines = []
}

function validSpots() {
  return (props.orderedSpots || []).filter(
    (spot) =>
      Number.isFinite(Number(spot.lng)) &&
      Number.isFinite(Number(spot.lat))
  )
}

function firstValidCoordinate() {
  const spots = validSpots()
  if (spots.length) return [Number(spots[0].lng), Number(spots[0].lat)]

  const origin = props.origin
  if (origin && Number.isFinite(Number(origin.lng)) && Number.isFinite(Number(origin.lat))) {
    return [Number(origin.lng), Number(origin.lat)]
  }
  return [116.397428, 39.90923]
}

function buildPolylinePath(spots) {
  const path = []
  const origin = props.origin
  if (
    origin &&
    Number.isFinite(Number(origin.lng)) &&
    Number.isFinite(Number(origin.lat))
  ) {
    path.push([Number(origin.lng), Number(origin.lat)])
  }
  spots.forEach((spot) => {
    path.push([Number(spot.lng), Number(spot.lat)])
  })
  const dest = props.destination || props.origin
  if (
    dest &&
    Number.isFinite(Number(dest.lng)) &&
    Number.isFinite(Number(dest.lat))
  ) {
    const last = path[path.length - 1]
    if (!last || dest.lng !== last[0] || dest.lat !== last[1]) {
      path.push([Number(dest.lng), Number(dest.lat)])
    }
  }
  return path
}

function markerLabel(spot) {
  return spot.name || ''
}

function markerContent(index) {
  return `<span style="
    display:inline-grid;
    width:28px;height:28px;
    place-items:center;
    border-radius:50%;
    color:#fff;
    background:#166534;
    font-weight:900;
    font-size:13px;
  ">${index + 1}</span>`
}

function startContent() {
  return `<span style="
    display:inline-grid;
    width:28px;height:28px;
    place-items:center;
    border-radius:50%;
    color:#fff;
    background:#2563eb;
    font-weight:900;
    font-size:11px;
  ">起</span>`
}

function drawMarkers(spots) {
  const origin = props.origin
  if (
    origin &&
    Number.isFinite(Number(origin.lng)) &&
    Number.isFinite(Number(origin.lat))
  ) {
    const startMarker = new AMap.Marker({
      position: [Number(origin.lng), Number(origin.lat)],
      content: startContent(),
      offset: new AMap.Pixel(-14, -28),
      title: origin.name || '起点',
      zIndex: 120,
    })
    startMarker.setMap(mapInstance)
    markers.push(startMarker)
  }

  spots.forEach((spot, index) => {
    const marker = new AMap.Marker({
      position: [Number(spot.lng), Number(spot.lat)],
      content: markerContent(index),
      offset: new AMap.Pixel(-14, -28),
      title: markerLabel(spot),
      zIndex: 110,
    })
    marker.setMap(mapInstance)
    markers.push(marker)
  })
}

function drawPolyline(path) {
  const polyline = new AMap.Polyline({
    path,
    strokeColor: '#166534',
    strokeWeight: 4,
    strokeOpacity: 0.7,
    strokeStyle: 'dashed',
    lineJoin: 'round',
    lineCap: 'round',
    zIndex: 90,
  })
  polyline.setMap(mapInstance)
  polylines.push(polyline)
}
</script>

<template>
  <div class="amap-wrapper">
    <div class="amap-header">
      <strong>高德地图路线</strong>
      <div class="amap-header-actions">
        <span v-if="totalDistance || totalDuration" class="amap-meta">
          {{ totalDistance }} · {{ totalDuration }}
        </span>
        <a v-if="navUrl" :href="navUrl" target="_blank" rel="noreferrer">打开高德地图</a>
      </div>
    </div>
    <div v-if="loadError" class="amap-error">{{ loadError }}</div>
    <div ref="container" class="amap-container"></div>
    <div class="amap-legend">
      <span v-if="origin" class="legend-item">
        <span class="legend-dot start"></span> 起点 {{ origin.name }}
      </span>
      <span v-for="(spot, index) in orderedSpots" :key="spot.id" class="legend-item">
        <span class="legend-dot" :style="{ background: '#166534' }">{{ index + 1 }}</span> {{ spot.name }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.amap-wrapper {
  border: 1px solid var(--line);
  border-radius: 22px;
  background: var(--panel-warm);
  overflow: hidden;
}

.amap-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
}

.amap-header strong {
  color: var(--text);
}

.amap-header-actions {
  display: flex;
  gap: 14px;
  align-items: center;
}

.amap-meta {
  color: var(--muted);
  font-size: 13px;
}

.amap-header a {
  color: var(--primary);
  font-weight: 800;
  text-decoration: none;
}

.amap-error {
  padding: 42px 16px;
  text-align: center;
  color: var(--muted);
}

.amap-container {
  width: 100%;
  min-height: 420px;
}

.amap-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px 16px;
  border-top: 1px solid var(--line);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}

.legend-dot {
  display: inline-grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #166534;
  font-weight: 900;
  font-size: 11px;
}

.legend-dot.start {
  background: #2563eb;
}
</style>