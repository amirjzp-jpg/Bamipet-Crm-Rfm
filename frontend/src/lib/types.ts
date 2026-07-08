/** Mirrors backend/app/schemas.py — keep in sync with the API contract. */

export interface User {
  id: number
  username: string
  role: 'admin' | 'viewer'
  language_pref: 'fa' | 'en'
  numerals_pref: 'western' | 'persian'
}

export interface SegmentMeta {
  code: string
  fa: string
  en: string
  color: string
  tone: string
}

export interface PersonaMeta {
  code: string
  fa: string
  en: string
  color: string
  description_en: string
  description_fa: string
}

export interface JourneyStageMeta {
  code: string
  fa: string
  en: string
}

export interface Meta {
  segments: SegmentMeta[]
  personas: PersonaMeta[]
  journey_stages: JourneyStageMeta[]
}

export interface SegmentCount {
  segment: string
  count: number
}

export interface Overview {
  run_date: string | null
  total_contacts: number
  segments: SegmentCount[]
}

export interface PersonaCount {
  persona: string
  confirmed: number
  inferred: number
  count: number
}

export interface PersonaOverview {
  run_date: string | null
  personas: PersonaCount[]
}

export interface ContactRow {
  contact_id: string
  display_name: string | null
  phone: string | null
  species: string | null
  segment: string | null
  persona_guess: string | null
  persona_confidence: string | null
  journey_stage: string | null
  lead_pillar: string | null
  r_score: number | null
  f_score: number | null
  m_score: number | null
  e_score: number | null
  recency_days: number | null
  order_count: number | null
  total_amount: number | null
  touch_count: number | null
  run_date: string | null
}

export interface ContactList {
  items: ContactRow[]
  total: number
  page: number
  page_size: number
}

export interface Snapshot {
  run_date: string
  recency_days: number | null
  order_count: number | null
  total_amount: number | null
  touch_count: number | null
  r_score: number | null
  f_score: number | null
  m_score: number | null
  e_score: number | null
  segment: string | null
  persona_guess: string | null
  persona_confidence: string | null
  lead_pillar: string | null
  journey_stage: string | null
}

export interface ContactDetail {
  contact_id: string
  display_name: string | null
  phone: string | null
  species: string | null
  latest: Snapshot | null
  history: Snapshot[]
}

export interface TrendPoint {
  run_date: string
  segment: string
  count: number
}

export interface MigrationCell {
  from_segment: string
  to_segment: string
  count: number
}

export interface Trends {
  series: TrendPoint[]
  run_dates: string[]
  migration: MigrationCell[]
  from_date: string | null
  to_date: string | null
}

export interface SyncRun {
  id: number
  started_at: string
  finished_at: string | null
  status: 'running' | 'success' | 'failed'
  trigger: string
  contacts_count: number | null
  orders_count: number | null
  calls_count: number | null
  sms_count: number | null
  error_message: string | null
}

export interface AdminConfig {
  navatel_mode: string
  base_url: string
  token_configured: boolean
  endpoints: Record<string, string>
  field_aliases: Record<string, Record<string, string>>
  lookback_days: number
  writeback_enabled: boolean
  writeback_fields: string[]
  nightly_sync_at: string
}
