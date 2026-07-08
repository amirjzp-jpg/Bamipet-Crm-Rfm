import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { login } from '@/lib/api'
import { Button } from '@/components/ui'

export default function Login() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(false)
    try {
      await login(username, password)
      navigate('/', { replace: true })
    } catch {
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-cream p-md">
      <div className="w-full max-w-sm">
        <div className="mb-lg text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-cobalt shadow-sheet">
            {/* companion mark placeholder — the real logo file replaces this asset */}
            <svg viewBox="0 0 32 32" className="h-9 w-9">
              <circle cx="11" cy="13" r="3.2" fill="#FAF9F6" />
              <circle cx="21" cy="13" r="3.2" fill="#FAF9F6" />
              <ellipse cx="16" cy="21" rx="5.5" ry="4.2" fill="#FAF9F6" />
            </svg>
          </div>
          <h1 className="text-2xl font-extrabold text-cobalt">{t('app.name')}</h1>
          <p className="mt-1 text-sm text-ink-muted">{t('app.subtitle')}</p>
        </div>

        <form onSubmit={submit} className="rounded-md border border-line bg-white p-lg shadow-sheet">
          <h2 className="mb-md text-lg font-bold">{t('login.title')}</h2>
          <label className="mb-1 block text-sm font-semibold text-ink-muted">{t('login.username')}</label>
          <input
            className="en mb-md w-full rounded-md border border-line-2 px-3 py-2 focus:border-cobalt focus:outline-none"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
          />
          <label className="mb-1 block text-sm font-semibold text-ink-muted">{t('login.password')}</label>
          <input
            type="password"
            className="en mb-md w-full rounded-md border border-line-2 px-3 py-2 focus:border-cobalt focus:outline-none"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          {error ? <p className="mb-md text-sm text-terracotta">{t('login.error')}</p> : null}
          <Button type="submit" disabled={busy || !username || !password}>
            {t('login.submit')}
          </Button>
        </form>
      </div>
    </div>
  )
}
