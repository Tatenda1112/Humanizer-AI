import { createClient } from '@/lib/supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Error types ────────────────────────────────────────────────
export class LimitExceededError extends Error {
  constructor(public details: { message: string; plan: string; limit: number; used: number }) {
    super('Word limit exceeded')
    this.name = 'LimitExceededError'
  }
}

// ── Interfaces ─────────────────────────────────────────────────
export interface HumanizeResponse {
  humanized_text: string
  words_used: number
  words_remaining: number | null
  mode_name: string
  provider: string
}

export interface DetectResponse {
  ai_score: number
  human_score: number
  sentences: string[]
}

export interface CompareResponse {
  before: DetectResponse
  after: DetectResponse
  improvement: number
}

export interface UserProfile {
  id: string
  email: string
  plan: 'free' | 'basic' | 'premium'
  preferred_provider: string
  words_used_today: number
  words_used_month: number
  daily_limit: number | null
  monthly_limit: number | null
  words_remaining_today: number | null
  words_remaining_month: number | null
  subscription_end_date: string | null
}

export interface Humanization {
  id: string
  original_text: string
  humanized_text: string
  original_preview: string
  humanized_preview: string
  word_count: number
  level: string
  tone: string
  ai_score_before: number | null
  ai_score_after: number | null
  provider: string
  created_at: string
}

// ── Core fetch wrapper ─────────────────────────────────────────
async function getToken(): Promise<string> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    window.location.href = '/login'
    throw new Error('Not authenticated')
  }
  return session.access_token
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = await getToken()
  const url = `${API_URL}${endpoint}`

  let res: Response
  try {
    res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    })
  } catch (networkErr) {
    throw new Error(`Cannot reach backend at ${url}. Is the FastAPI server running on port 8000? (${networkErr})`)
  }

  if (res.status === 401) {
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (res.status === 429) {
    const body = await res.json()
    throw new LimitExceededError(body.detail)
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }

  return res.json() as Promise<T>
}

// ── Public API functions ───────────────────────────────────────
export async function humanizeText(
  text: string,
  level: string,
  tone: string,
  mode: string = 'ghost_2'
): Promise<HumanizeResponse> {
  return apiFetch<HumanizeResponse>('/humanize', {
    method: 'POST',
    body: JSON.stringify({ text, level, tone, mode }),
  })
}

export async function detectAI(text: string): Promise<DetectResponse> {
  return apiFetch<DetectResponse>('/detect', {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export async function compareScores(
  original: string,
  humanized: string
): Promise<CompareResponse> {
  return apiFetch<CompareResponse>('/detect/compare', {
    method: 'POST',
    body: JSON.stringify({ original, humanized }),
  })
}

export async function getProfile(): Promise<UserProfile> {
  return apiFetch<UserProfile>('/user/me')
}

export async function getHistory(): Promise<Humanization[]> {
  return apiFetch<Humanization[]>('/user/history')
}

export async function createCheckout(plan: string): Promise<{ url: string }> {
  return apiFetch<{ url: string }>('/stripe/checkout', {
    method: 'POST',
    body: JSON.stringify({ plan }),
  })
}

export async function getPortal(): Promise<{ url: string }> {
  return apiFetch<{ url: string }>('/stripe/portal')
}
