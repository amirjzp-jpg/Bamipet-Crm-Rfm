import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'

import { Button, Card, PageHeader, Spinner } from '@/components/ui'
import { api, ApiError } from '@/lib/api'
import { applyLang } from '@/i18n'
import { useMe } from '@/lib/hooks'

export default function Settings() {
  const { t } = useTranslation()
  const { data: me, isLoading } = useMe()
  const queryClient = useQueryClient()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [pwMessage, setPwMessage] = useState<'ok' | 'err' | null>(null)

  if (isLoading || !me) return <Spinner />

  async function setPrefs(prefs: { language_pref?: 'fa' | 'en'; numerals_pref?: 'western' | 'persian' }) {
    await api('/me/prefs', { method: 'PATCH', body: JSON.stringify(prefs) })
    if (prefs.language_pref) applyLang(prefs.language_pref)
    queryClient.invalidateQueries({ queryKey: ['me'] })
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault()
    setPwMessage(null)
    try {
      await api('/me/password', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      })
      setPwMessage('ok')
      setCurrentPassword('')
      setNewPassword('')
    } catch (err) {
      if (err instanceof ApiError) setPwMessage('err')
    }
  }

  function Choice({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
    return (
      <button
        onClick={onClick}
        className={`rounded-md border px-4 py-2 text-sm font-semibold transition-colors ${
          active ? 'border-cobalt bg-cobalt text-white' : 'border-line-2 text-ink-muted hover:bg-mist'
        }`}
      >
        {children}
      </button>
    )
  }

  return (
    <>
      <PageHeader title={t('settings.title')} />
      <div className="max-w-xl space-y-md">
        <Card className="p-md">
          <h2 className="mb-sm font-bold">{t('settings.language')}</h2>
          <div className="flex gap-2">
            <Choice active={me.language_pref === 'fa'} onClick={() => setPrefs({ language_pref: 'fa' })}>
              {t('settings.fa')}
            </Choice>
            <Choice active={me.language_pref === 'en'} onClick={() => setPrefs({ language_pref: 'en' })}>
              <span className="en">{t('settings.en')}</span>
            </Choice>
          </div>
        </Card>

        <Card className="p-md">
          <h2 className="mb-1 font-bold">{t('settings.numerals')}</h2>
          <p className="mb-sm text-xs text-ink-muted">{t('settings.numeralsNote')}</p>
          <div className="flex gap-2">
            <Choice active={me.numerals_pref === 'western'} onClick={() => setPrefs({ numerals_pref: 'western' })}>
              {t('settings.western')}
            </Choice>
            <Choice active={me.numerals_pref === 'persian'} onClick={() => setPrefs({ numerals_pref: 'persian' })}>
              {t('settings.persian')}
            </Choice>
          </div>
        </Card>

        <Card className="p-md">
          <h2 className="mb-sm font-bold">{t('settings.changePassword')}</h2>
          <form onSubmit={changePassword} className="space-y-2">
            <input type="password" className="en w-full rounded-md border border-line-2 px-3 py-2 text-sm"
              placeholder={t('settings.currentPassword')} value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)} autoComplete="current-password" />
            <input type="password" className="en w-full rounded-md border border-line-2 px-3 py-2 text-sm"
              placeholder={t('settings.newPassword')} value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" />
            {pwMessage === 'ok' ? <p className="text-sm text-green">{t('settings.passwordChanged')}</p> : null}
            {pwMessage === 'err' ? <p className="text-sm text-terracotta">{t('settings.passwordError')}</p> : null}
            <Button type="submit" disabled={!currentPassword || newPassword.length < 8}>
              {t('settings.save')}
            </Button>
          </form>
        </Card>
      </div>
    </>
  )
}
