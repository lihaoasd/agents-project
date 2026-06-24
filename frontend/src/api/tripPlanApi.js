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

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}