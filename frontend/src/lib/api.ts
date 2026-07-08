/** Minimal typed API client with JWT storage + automatic refresh-and-retry
 * on 401. Tokens in localStorage — acceptable for an internal tool behind
 * team logins; the API enforces all real authorization server-side. */

const BASE = '/api/v1'

export interface TokenPair {
  access_token: string
  refresh_token: string
}

export function getTokens(): TokenPair | null {
  const raw = localStorage.getItem('bamipet_tokens')
  return raw ? (JSON.parse(raw) as TokenPair) : null
}

export function setTokens(t: TokenPair | null) {
  if (t) localStorage.setItem('bamipet_tokens', JSON.stringify(t))
  else localStorage.removeItem('bamipet_tokens')
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function refreshTokens(): Promise<boolean> {
  const tokens = getTokens()
  if (!tokens) return false
  const resp = await fetch(`${BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: tokens.refresh_token }),
  })
  if (!resp.ok) {
    setTokens(null)
    return false
  }
  setTokens((await resp.json()) as TokenPair)
  return true
}

export async function api<T>(path: string, options: RequestInit = {}, retried = false): Promise<T> {
  const tokens = getTokens()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  if (tokens) headers.Authorization = `Bearer ${tokens.access_token}`

  const resp = await fetch(`${BASE}${path}`, { ...options, headers })
  if (resp.status === 401 && !retried && tokens) {
    if (await refreshTokens()) return api<T>(path, options, true)
    window.location.assign('/login')
    throw new ApiError(401, 'Session expired')
  }
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail ?? detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(resp.status, detail)
  }
  if (resp.status === 204) return undefined as T
  return (await resp.json()) as T
}

export async function login(username: string, password: string): Promise<void> {
  const resp = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new ApiError(resp.status, body.detail)
  }
  setTokens((await resp.json()) as TokenPair)
}

export function logout() {
  setTokens(null)
  window.location.assign('/login')
}

/** Authenticated file download (CSV export) via blob + anchor click. */
export async function downloadFile(path: string, filename: string) {
  const tokens = getTokens()
  const resp = await fetch(`${BASE}${path}`, {
    headers: tokens ? { Authorization: `Bearer ${tokens.access_token}` } : {},
  })
  if (!resp.ok) throw new ApiError(resp.status, 'Download failed')
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
