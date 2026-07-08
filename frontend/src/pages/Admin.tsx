import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'

import { Button, Card, ErrorBox, PageHeader, Spinner } from '@/components/ui'
import { api } from '@/lib/api'
import { fmtDate, fmtNum } from '@/lib/format'
import { useAdminConfig, useLabels, useMe, useSyncRuns } from '@/lib/hooks'
import type { User } from '@/lib/types'
import { useQuery } from '@tanstack/react-query'

export default function Admin() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const queryClient = useQueryClient()
  const runs = useSyncRuns(5000) // live-poll while this page is open
  const config = useAdminConfig()
  const users = useQuery<User[]>({ queryKey: ['users'], queryFn: () => api('/users') })
  const { lang } = useLabels()
  const numerals = me?.numerals_pref ?? 'western'

  const [triggering, setTriggering] = useState(false)
  const [newUsername, setNewUsername] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newRole, setNewRole] = useState<'viewer' | 'admin'>('viewer')

  const anyRunning = runs.data?.some((r) => r.status === 'running') ?? false

  async function triggerSync() {
    setTriggering(true)
    try {
      await api('/sync-runs/trigger', { method: 'POST' })
      queryClient.invalidateQueries({ queryKey: ['sync-runs'] })
    } finally {
      setTriggering(false)
    }
  }

  async function createUser(e: React.FormEvent) {
    e.preventDefault()
    await api('/users', { method: 'POST', body: JSON.stringify({ username: newUsername, password: newPassword, role: newRole }) })
    setNewUsername('')
    setNewPassword('')
    queryClient.invalidateQueries({ queryKey: ['users'] })
  }

  async function deleteUser(id: number) {
    await api(`/users/${id}`, { method: 'DELETE' })
    queryClient.invalidateQueries({ queryKey: ['users'] })
  }

  if (runs.isLoading || config.isLoading) return <Spinner />
  if (runs.isError) return <ErrorBox onRetry={() => runs.refetch()} />

  const statusLabel = { success: t('sync.success'), failed: t('sync.failed'), running: t('sync.runningStatus') }
  const statusColor = { success: 'text-green', failed: 'text-terracotta', running: 'text-amber' }
  const triggerLabel: Record<string, string> = { scheduled: t('sync.scheduled'), manual: t('sync.manual'), seed: t('sync.seed') }

  return (
    <>
      <PageHeader title={t('sync.title')} />

      {config.data?.navatel_mode === 'mock' ? (
        <div className="mb-md rounded-md border border-amber-line bg-amber-bg px-md py-3 text-sm text-amber-deep">
          {t('sync.mockNote')}
        </div>
      ) : null}

      <div className="grid gap-md lg:grid-cols-3">
        {/* run history */}
        <Card className="overflow-x-auto lg:col-span-2">
          <div className="flex items-center justify-between px-md pt-md">
            <h2 className="font-bold">{t('sync.history')}</h2>
            <Button onClick={triggerSync} disabled={triggering || anyRunning}>
              {anyRunning ? t('sync.running') : t('sync.runNow')}
            </Button>
          </div>
          <table className="mt-sm w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-mist text-xs text-ink-muted">
                <th className="px-3 py-2 text-start font-semibold">{t('sync.id')}</th>
                <th className="px-3 py-2 text-start font-semibold">{t('sync.started')}</th>
                <th className="px-3 py-2 text-start font-semibold">{t('sync.status')}</th>
                <th className="px-3 py-2 text-start font-semibold">{t('sync.trigger')}</th>
                <th className="px-3 py-2 text-start font-semibold">{t('sync.records')}</th>
              </tr>
            </thead>
            <tbody>
              {runs.data?.map((r) => (
                <tr key={r.id} className="border-b border-line last:border-0">
                  <td className="num px-3 py-2">{r.id}</td>
                  <td className="px-3 py-2">{fmtDate(r.started_at, lang, numerals)}</td>
                  <td className={`px-3 py-2 font-semibold ${statusColor[r.status]}`}>
                    {statusLabel[r.status]}
                    {r.error_message ? (
                      <div className="en max-w-64 truncate text-[10px] font-normal text-ink-faint" title={r.error_message}>
                        {r.error_message}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-3 py-2">{triggerLabel[r.trigger] ?? r.trigger}</td>
                  <td className="num px-3 py-2 text-xs">
                    {r.contacts_count !== null
                      ? `${fmtNum(r.contacts_count, numerals)}C · ${fmtNum(r.orders_count, numerals)}O · ${fmtNum(r.calls_count, numerals)}L · ${fmtNum(r.sms_count, numerals)}S`
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* config + users */}
        <div className="space-y-md">
          <Card className="p-md">
            <h2 className="mb-sm font-bold">{t('sync.config')}</h2>
            {config.data ? (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-ink-muted">{t('sync.mode')}</dt>
                  <dd className={`font-semibold ${config.data.navatel_mode === 'live' ? 'text-green' : 'text-amber'}`}>
                    {config.data.navatel_mode === 'live' ? t('sync.modeLive') : t('sync.modeMock')}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">Token</dt>
                  <dd className={config.data.token_configured ? 'text-green' : 'text-ink-faint'}>
                    {config.data.token_configured ? t('sync.tokenSet') : t('sync.tokenMissing')}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">{t('sync.writeback')}</dt>
                  <dd>{config.data.writeback_enabled ? t('sync.on') : t('sync.off')}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">{t('sync.nightly')}</dt>
                  <dd className="num">{config.data.nightly_sync_at}</dd>
                </div>
                <div className="border-t border-line pt-2">
                  <dt className="mb-1 text-ink-muted">Endpoints</dt>
                  {Object.entries(config.data.endpoints).map(([k, v]) => (
                    <dd key={k} className="en truncate text-[11px] text-ink-faint" title={v}>
                      {k}: {v}
                    </dd>
                  ))}
                </div>
              </dl>
            ) : null}
          </Card>

          <Card className="p-md">
            <h2 className="mb-sm font-bold">{t('sync.users')}</h2>
            <ul className="mb-md space-y-1.5">
              {users.data?.map((u) => (
                <li key={u.id} className="flex items-center justify-between text-sm">
                  <span className="en">{u.username}
                    <span className="ms-2 text-[10px] text-ink-faint">{u.role === 'admin' ? t('sync.admin') : t('sync.viewer')}</span>
                  </span>
                  {u.id !== me?.id ? (
                    <button onClick={() => deleteUser(u.id)} className="text-xs text-terracotta hover:underline">
                      {t('sync.delete')}
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
            <form onSubmit={createUser} className="space-y-2">
              <input className="en w-full rounded-md border border-line-2 px-3 py-1.5 text-sm" placeholder={t('sync.newUsername')}
                value={newUsername} onChange={(e) => setNewUsername(e.target.value)} />
              <input type="password" className="en w-full rounded-md border border-line-2 px-3 py-1.5 text-sm" placeholder={t('sync.newPassword')}
                value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              <div className="flex items-center gap-2">
                <select className="rounded-md border border-line-2 bg-white px-2 py-1.5 text-sm" value={newRole}
                  onChange={(e) => setNewRole(e.target.value as 'viewer' | 'admin')}>
                  <option value="viewer">{t('sync.viewer')}</option>
                  <option value="admin">{t('sync.admin')}</option>
                </select>
                <Button type="submit" disabled={newUsername.length < 3 || newPassword.length < 8}>
                  {t('sync.create')}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </>
  )
}
