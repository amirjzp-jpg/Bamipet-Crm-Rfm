/** React Query hooks over the API contract + display-label helpers that
 * resolve segment/persona codes through the backend's meta registry
 * (single source of truth — no labels or colors hardcoded client-side). */
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { api } from './api'
import type {
  AdminConfig, ContactDetail, ContactList, Meta, Overview,
  PersonaOverview, SyncRun, Trends, User,
} from './types'

export function useMe() {
  return useQuery<User>({ queryKey: ['me'], queryFn: () => api('/me'), staleTime: 60_000 })
}

export function useMeta() {
  return useQuery<Meta>({ queryKey: ['meta'], queryFn: () => api('/segments/meta'), staleTime: Infinity })
}

export function useOverview() {
  return useQuery<Overview>({ queryKey: ['overview'], queryFn: () => api('/segments/overview') })
}

export function usePersonaOverview() {
  return useQuery<PersonaOverview>({ queryKey: ['personas'], queryFn: () => api('/personas/overview') })
}

export function useContacts(params: Record<string, string | number>) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== '' && v !== undefined).map(([k, v]) => [k, String(v)]),
  ).toString()
  return useQuery<ContactList>({ queryKey: ['contacts', qs], queryFn: () => api(`/contacts?${qs}`) })
}

export function useContactDetail(contactId: string) {
  return useQuery<ContactDetail>({
    queryKey: ['contact', contactId],
    queryFn: () => api(`/contacts/${encodeURIComponent(contactId)}`),
  })
}

export function useTrends(from?: string, to?: string) {
  const qs = new URLSearchParams()
  if (from) qs.set('from', from)
  if (to) qs.set('to', to)
  return useQuery<Trends>({
    queryKey: ['trends', from, to],
    queryFn: () => api(`/trends/segment-migration?${qs.toString()}`),
  })
}

export function useSyncRuns(refetchMs?: number) {
  return useQuery<SyncRun[]>({
    queryKey: ['sync-runs'],
    queryFn: () => api('/sync-runs?limit=30'),
    refetchInterval: refetchMs,
  })
}

export function useAdminConfig() {
  return useQuery<AdminConfig>({ queryKey: ['admin-config'], queryFn: () => api('/admin/config') })
}

/** Label helpers bound to the active language. */
export function useLabels() {
  const { data: meta } = useMeta()
  const { i18n } = useTranslation()
  const lang = (i18n.language === 'en' ? 'en' : 'fa') as 'fa' | 'en'

  return {
    lang,
    meta,
    segmentLabel(code: string | null | undefined): string {
      if (!code) return '—'
      const s = meta?.segments.find((x) => x.code === code)
      return s ? s[lang] : code
    },
    segmentColor(code: string | null | undefined): string {
      return meta?.segments.find((x) => x.code === code)?.color ?? '#8B93A5'
    },
    personaColor(code: string | null | undefined): string {
      return meta?.personas.find((x) => x.code === code)?.color ?? '#8B93A5'
    },
    stageLabel(code: string | null | undefined): string {
      if (!code) return '—'
      const s = meta?.journey_stages.find((x) => x.code === code)
      return s ? s[lang] : code
    },
  }
}
