/** 行程规划 API 层。 */

const BASE_URL = 'http://127.0.0.1:8000'

/**
 * 根据用户文化旅行需求生成地方推荐。
 * @param {string} requirement - 用户原始需求文本
 * @returns {Promise<{ data: { destinations: Array, notice: string }, meta: object }>}
 */
export async function recommendPlaces(requirement) {
  const response = await fetch(`${BASE_URL}/api/trip-plan/place-recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ requirement }),
  })
  const body = await response.json()
  if (!response.ok) {
    throw new ApiError(body?.detail || body?.error?.message || '请求失败', response.status)
  }
  return body
}

/**
 * 根据用户需求和选定目的地生成景点推荐。
 * @param {{ requirement: string, destinationId: string, destinationCity: string, destinationProvince: string }} params
 * @returns {Promise<{ data: { spots: Array, notice: string }, meta: object }>}
 */
export async function recommendScenicSpots({ requirement, destinationId, destinationCity, destinationProvince }) {
  const response = await fetch(`${BASE_URL}/api/trip-plan/scenic-spots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ requirement, destinationId, destinationCity, destinationProvince }),
  })
  const body = await response.json()
  if (!response.ok) {
    throw new ApiError(body?.detail || body?.error?.message || '请求失败', response.status)
  }
  return body
}

/**
 * 根据用户需求和已选景点生成综合文化解读。
 * @param {{ requirement: string, destinationId: string, destinationCity: string, destinationProvince: string, spots: Array }} params
 * @returns {Promise<{ data: { cultures: Array, notice: string }, meta: object }>}
 */
export async function recommendCulturalInterpretations({
  requirement,
  destinationId,
  destinationCity,
  destinationProvince,
  spots,
}) {
  const response = await fetch(`${BASE_URL}/api/trip-plan/cultural-interpretations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      requirement,
      destinationId,
      destinationCity,
      destinationProvince,
      spots,
    }),
  })
  const body = await response.json()
  if (!response.ok) {
    throw new ApiError(body?.detail || body?.error?.message || '请求失败', response.status)
  }
  return body
}

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}