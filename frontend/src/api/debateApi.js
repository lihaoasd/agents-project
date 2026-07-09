const BASE = 'http://127.0.0.1:8000'

/** 为角色生成默认头像 */
function defaultAvatar(role) {
  const map = {
    '儒家': '📖', '道家': '☯️', '法家': '⚖️', '墨家': '🛡️', '兵家': '⚔️',
    '心学': '💡', '理学': '🔬',
    '古希腊哲学': '🏛️', '德国古典哲学': '📜', '马克思主义': '🔨',
    '政治现实主义': '🏰', '社会契约论': '🤝', '自由主义': '🕊️',
    '古典经济学': '💰', '凯恩斯主义': '📊', '奥地利学派': '🏦',
    '社会学': '👥', '心理学': '🧠', '人类学': '🌍',
    '语言学': '🗣️', '传播学': '📡', '政治学': '🏛️',
    '科学哲学': '🔭', '政治哲学': '📯', '进化生物学': '🧬',
    '集大成者': '👑',
  }
  return map[role.school] || map[role.style] || '🎭'
}

export async function fetchRoles() {
  const res = await fetch(`${BASE}/api/debate/roles`)
  if (!res.ok) throw new Error(`获取角色列表失败: ${res.status}`)
  const raw = await res.json()
  // 后端直接返回 { debaters: [...], judges: [...] }，无 data 包裹
  // 补全前端需要的字段
  return {
    debaters: (raw.debaters || []).map(r => ({
      ...r,
      avatar: r.avatar || defaultAvatar(r),
      persona_short: r.persona_short || r.description || '',
      period: r.period || r.era || '',
    })),
    judges: (raw.judges || []).map(j => ({
      ...j,
      avatar: j.avatar || '⚖️',
      persona_short: j.persona_short || j.description || '',
    })),
  }
}

export async function startDebate({ question, debater_ids, judge_id, cross_examination_rounds }) {
  const res = await fetch(`${BASE}/api/debate/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, debater_ids, judge_id, cross_examination_rounds }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `发起辩论失败: ${res.status}`)
  }
  // 后端直接返回 { session_id, question, debaters, judge, ... }
  const raw = await res.json()
  return {
    session_id: raw.session_id,
    question: raw.question,
    debaters: (raw.debaters || []).map(d => ({
      ...d,
      avatar: d.avatar || defaultAvatar(d),
      school: d.school || '',
    })),
    judge: raw.judge ? { ...raw.judge, avatar: raw.judge.avatar || '⚖️' } : null,
    cross_examination_rounds: raw.cross_examination_rounds,
  }
}

export function getStreamUrl(sessionId) {
  return `${BASE}/api/debate/stream/${sessionId}`
}

export async function fetchSession(sessionId) {
  const res = await fetch(`${BASE}/api/debate/sessions/${sessionId}`)
  if (res.status === 409) return null
  if (!res.ok) throw new Error(`获取会话失败: ${res.status}`)
  return res.json()
}

export function getExportUrl(sessionId, format) {
  return `${BASE}/api/debate/sessions/${sessionId}/export?format=${format}`
}
