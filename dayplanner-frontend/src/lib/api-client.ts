declare const process: { env: Record<string, string | undefined> }

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

const ACCESS_TOKEN_KEY = 'dp_access_token'
const USER_ID_KEY = 'dp_user_id'

export function getLocalDateISO(): string {
  const now = new Date()
  const offsetMinutes = now.getTimezoneOffset()
  const local = new Date(now.getTime() - offsetMinutes * 60_000)
  return local.toISOString().slice(0, 10)
}

export function getStoredAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function clearAuthSession(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(USER_ID_KEY)
}

function persistAuthSession(accessToken: string, userId: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(USER_ID_KEY, userId)
}

function requireAccessToken(): string {
  const token = getStoredAccessToken()
  if (!token) {
    throw new Error('Authentication required')
  }
  return token
}

function decodeJwtSubject(token: string): string | null {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    const payload = JSON.parse(atob(parts[1]))
    if (typeof payload?.sub === 'string' && payload.sub.trim()) {
      return payload.sub
    }
    return null
  } catch {
    return null
  }
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const token = requireAccessToken()
  let userId = localStorage.getItem(USER_ID_KEY) || ''
  if (!userId) {
    const decoded = decodeJwtSubject(token)
    if (decoded) {
      userId = decoded
      localStorage.setItem(USER_ID_KEY, decoded)
    }
  }
  return {
    Authorization: `Bearer ${token}`,
    'X-User-Id': userId,
    'Content-Type': 'application/json',
  }
}

export type AuthPayload = {
  access_token: string
  token_type: string
  user_id: string
}

export async function signup(email: string, fullName: string, password: string): Promise<AuthPayload> {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, full_name: fullName, password }),
  })
  if (!response.ok) {
    throw new Error('Signup failed')
  }
  const payload = await response.json()
  persistAuthSession(payload.access_token, payload.user_id)
  return payload
}

export async function login(email: string, password: string): Promise<AuthPayload> {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) {
    throw new Error('Login failed')
  }
  const payload = await response.json()
  persistAuthSession(payload.access_token, payload.user_id)
  return payload
}

export async function startGoogleLogin(): Promise<{ redirect_url: string; scope?: string }> {
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/google/start`, { method: 'GET' })
  if (!response.ok) {
    throw new Error('Unable to start Google login')
  }
  return response.json()
}

export async function completeGoogleCallback(code: string, state: string): Promise<void> {
  const response = await fetch(
    `${BACKEND_URL}/api/v1/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
    {
    method: 'GET',
    }
  )
  if (!response.ok) {
    throw new Error('Failed to complete Google callback')
  }
  const payload = await response.json()
  persistAuthSession(payload.access_token, payload.user_id || 'dev-user')
}

export type MeResponse = {
  user_id: string
  email: string
  full_name: string
}

export async function getMe(): Promise<MeResponse> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Unable to load profile')
  }
  return response.json()
}

export async function bootstrapFrontendInitialization(): Promise<void> {
  await getMe()
  await getSettings()
  await getCalendarAccounts()
}

export type ApiPlanBlock = {
  id: string
  title: string
  start_time: string
  end_time: string
  priority: 'high' | 'medium' | 'low'
  category: string
  completed: boolean
}

export type ApiPlan = {
  id: string
  date: string
  summary: string
  blocks: ApiPlanBlock[]
}

export async function getTodayPlan(date: string): Promise<ApiPlan> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/plans/today?date=${encodeURIComponent(date)}`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load today plan')
  }
  return response.json()
}

export async function updatePlanBlock(planId: string, blockId: string, completed: boolean): Promise<void> {
  const headers = await getAuthHeaders()
  const response = await fetch(
    `${BACKEND_URL}/api/v1/plans/${planId}/blocks/${blockId}?completed=${completed ? 'true' : 'false'}`,
    {
      method: 'PATCH',
      headers,
    }
  )
  if (!response.ok) {
    throw new Error('Failed to update block')
  }
}

export async function startEveningCheckin(planId: string): Promise<{ status: string; plan_id: string; message: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/plans/${planId}/evening-checkin`, {
    method: 'POST',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to start evening check-in')
  }
  return response.json()
}

export async function createChatSession(): Promise<{ session_id: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/chat/sessions`, {
    method: 'POST',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to create chat session')
  }
  return response.json()
}

export async function sendChatMessage(
  sessionId: string,
  content: string,
  planDate?: string
): Promise<{
  message: string
  summary: string
  assistant_reply: string
  needs_clarification: boolean
  follow_up_questions: string[]
  blocks: ApiPlanBlock[]
}> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ content, plan_date: planDate || getLocalDateISO() }),
  })
  if (!response.ok) {
    throw new Error('Failed to send message')
  }
  return response.json()
}

export type StreamEvent =
  | { type: 'token'; content: string }
  | { type: 'plan'; blocks: ApiPlanBlock[]; summary: string; saved: boolean }
  | { type: 'done' }
  | { type: 'error'; message: string }

export async function sendMessageStream(
  sessionId: string,
  content: string,
  planDate: string,
  onToken: (token: string) => void,
  onPlan: (blocks: ApiPlanBlock[], summary: string, saved: boolean) => void,
  onDone: () => void,
  onError: (message: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const headers = await getAuthHeaders()

  const response = await fetch(
    `${BACKEND_URL}/api/v1/chat/sessions/${sessionId}/messages/stream`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({ content, plan_date: planDate }),
      signal,
    }
  )

  if (!response.ok) {
    onError(`Request failed: ${response.status}`)
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError('No response body')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const event: StreamEvent = JSON.parse(line.slice(6))
        if (event.type === 'token') onToken(event.content)
        else if (event.type === 'plan') onPlan(event.blocks, event.summary, event.saved)
        else if (event.type === 'done') onDone()
        else if (event.type === 'error') onError(event.message)
      } catch {
      }
    }
  }
}

export type ApiCalendarAccount = {
  id: string
  provider: string
  email: string
  status: string
  last_synced_at: string | null
}

export type ApiCalendarConflict = {
  id: string
  description: string
  status: string
}

export async function getCalendarAccounts(): Promise<ApiCalendarAccount[]> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/calendar/accounts`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load calendar accounts')
  }
  return response.json()
}

export async function syncCalendarAccounts(): Promise<void> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/calendar/sync-all`, {
    method: 'POST',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to sync calendar accounts')
  }
}

export async function getCalendarConflicts(date: string): Promise<ApiCalendarConflict[]> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/calendar/conflicts?date=${encodeURIComponent(date)}`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load calendar conflicts')
  }
  return response.json()
}

export async function resolveCalendarConflict(conflictId: string, resolution: string = 'accept_ai_suggestion'): Promise<ApiCalendarConflict> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/calendar/conflicts/${conflictId}/resolve`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ resolution }),
  })
  if (!response.ok) {
    throw new Error('Failed to resolve calendar conflict')
  }
  return response.json()
}

export async function startGoogleCalendarConnect(): Promise<{ redirect_url: string; scope?: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/calendar/accounts/google/start`, {
    method: 'POST',
    headers,
  })
  if (!response.ok) {
    let detail = 'Failed to start Google calendar connect'
    try {
      const payload = await response.json()
      if (payload?.detail) detail = String(payload.detail)
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function completeGoogleCalendarConnect(code: string, state: string): Promise<{ status: string; provider: string; email: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(
    `${BACKEND_URL}/api/v1/calendar/accounts/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
    {
    method: 'POST',
    headers,
    }
  )
  if (!response.ok) {
    let detail = 'Failed to complete Google calendar connect'
    try {
      const payload = await response.json()
      if (payload?.detail) detail = String(payload.detail)
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }
  return response.json()
}

export type ApiHistorySummary = {
  completion_rate: number
  streak_days: number
  memory_patterns_count: number
}

export type ApiWeeklyPerformance = {
  day: string
  completion: number
}

export type ApiArchivedPlan = {
  id: string
  date: string
  tasks_planned: number
  completion_rate: number
  status: string
}

export async function getHistorySummary(range: '7d' | '30d' = '7d'): Promise<ApiHistorySummary> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/history/summary?range=${encodeURIComponent(range)}`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load history summary')
  }
  return response.json()
}

export async function getWeeklyPerformance(): Promise<ApiWeeklyPerformance[]> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/history/weekly-performance`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load weekly performance')
  }
  return response.json()
}

export async function getArchivedPlans(): Promise<ApiArchivedPlan[]> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/history/plans`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load archived plans')
  }
  return response.json()
}

export type ApiSettings = {
  timezone: string
  planning_style: string
  morning_briefing_time: string
  evening_checkin_time: string
  notifications_enabled: boolean
  privacy_mode: string
}

export type ApiMemoryItem = {
  id: string
  node_type: string
  content: string
  confidence: string
}

export type ApiMemoryContext = {
  snippets: string[]
  items: ApiMemoryItem[]
}

export type ApiNotification = {
  id: string
  kind: string
  message: string
  is_read: boolean
  created_at: string
}

export type ApiProviderModel = {
  id: string
  name: string
}

export type ApiLLMConfig = {
  primary_provider: string
  primary_api_key: string
  primary_model: string
  fallback_provider: string
  fallback_api_key: string
  fallback_model: string
  usage_alert_enabled: boolean
  usage_alert_threshold_pct: number
}

export async function getSettings(): Promise<ApiSettings> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/settings`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load settings')
  }
  return response.json()
}

export async function updateSettings(payload: Partial<ApiSettings>): Promise<ApiSettings> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/settings`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error('Failed to update settings')
  }
  return response.json()
}

export async function listNotifications(): Promise<ApiNotification[]> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/settings/notifications`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load notifications')
  }
  return response.json()
}

export async function listProviderModels(provider: string, apiKey: string): Promise<ApiProviderModel[]> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/settings/llm/models`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ provider, api_key: apiKey }),
  })
  if (!response.ok) {
    throw new Error('Failed to load provider models')
  }
  const payload = await response.json()
  return payload.models || []
}

export async function getLLMConfig(): Promise<ApiLLMConfig> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/settings/llm/config`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load LLM config')
  }
  return response.json()
}

export async function updateLLMConfig(payload: ApiLLMConfig): Promise<ApiLLMConfig> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/settings/llm/config`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error('Failed to update LLM config')
  }
  return response.json()
}

export async function checkLLMUsageLimit(): Promise<{ provider: string; usage_pct: number; alert_triggered: boolean }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/settings/llm/usage-check`, {
    method: 'POST',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to check LLM usage')
  }
  return response.json()
}

export async function resetMemory(): Promise<void> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/memory/reset`, {
    method: 'POST',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to reset memory')
  }
}

export async function getMemoryContext(query: string = 'today planning'): Promise<ApiMemoryContext> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/memory/context?query=${encodeURIComponent(query)}`, {
    method: 'GET',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to load memory context')
  }
  return response.json()
}

export async function addMemoryItem(content: string, nodeType: string = 'note', confidence: string = 'medium'): Promise<ApiMemoryItem> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/memory/context`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ content, node_type: nodeType, confidence }),
  })
  if (!response.ok) {
    throw new Error('Failed to add memory item')
  }
  return response.json()
}

export async function deleteMemoryItem(memoryId: string): Promise<void> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/api/v1/memory/context/${memoryId}`, {
    method: 'DELETE',
    headers,
  })
  if (!response.ok) {
    throw new Error('Failed to delete memory item')
  }
}
