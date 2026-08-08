const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

async function parseResponse(response) {
  let data
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const message = data?.detail || `请求失败（HTTP ${response.status}）`
    throw new Error(message)
  }
  return data
}

export async function checkHealth(signal) {
  const response = await fetch(`${API_BASE}/health`, { signal })
  return parseResponse(response)
}

export async function searchKnowledge(payload, signal) {
  const response = await fetch(`${API_BASE}/v1/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  return parseResponse(response)
}

