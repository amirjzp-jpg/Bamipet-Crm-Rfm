/** App shell: sidebar (mirrors right in RTL automatically via flex + dir),
 * topbar with language toggle and user menu. Farsi-first per spec §4.8. */
import { NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { logout } from '@/lib/api'
import { useMe, useSyncRuns } from '@/lib/hooks'
import { applyLang } from '@/i18n'
import { api } from '@/lib/api'
import { fmtDateShort } from '@/lib/format'
import { useQueryClient } from '@tanstack/react-query'

const NAV = [
  { to: '/', key: 'overview', icon: 'M4 13h6V4H4v9zm0 7h6v-5H4v5zm10 0h6V11h-6v9zm0-16v5h6V4h-6z' },
  { to: '/customers', key: 'customers', icon: 'M16 11c1.66 0 3-1.34 3-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 3-1.34 3-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13zm8 0c-.29 0-.62.02-.97.05C16.19 13.89 17 15.02 17 16.5V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z' },
  { to: '/trends', key: 'trends', icon: 'M3.5 18.5l6-6 4 4L22 7.92 20.59 6.5l-7.09 8-4-4L2 18l1.5.5z' },
  { to: '/sync', key: 'sync', icon: 'M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z', admin: true },
  { to: '/settings', key: 'settings', icon: 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z' },
]

export default function Layout() {
  const { t, i18n } = useTranslation()
  const { data: me } = useMe()
  const { data: runs } = useSyncRuns()
  const queryClient = useQueryClient()
  const lang = i18n.language === 'en' ? 'en' : 'fa'
  const lastOk = runs?.find((r) => r.status === 'success')

  async function switchLang() {
    const next = lang === 'fa' ? 'en' : 'fa'
    applyLang(next)
    // persist as the user's server-side preference too (spec §4.8)
    api('/me/prefs', { method: 'PATCH', body: JSON.stringify({ language_pref: next }) })
      .then(() => queryClient.invalidateQueries({ queryKey: ['me'] }))
      .catch(() => {})
  }

  return (
    <div className="flex min-h-screen">
      {/* sidebar — start-side: right in RTL, left in LTR */}
      <aside className="flex w-60 shrink-0 flex-col border-e border-line bg-white">
        <div className="border-b border-line px-md py-5">
          <div className="text-xl font-extrabold text-cobalt">{t('app.name')}</div>
          <div className="mt-0.5 text-[11px] leading-5 text-ink-faint">{t('app.subtitle')}</div>
        </div>
        <nav className="flex-1 space-y-1 p-sm pt-md">
          {NAV.filter((n) => !n.admin || me?.role === 'admin').map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-semibold transition-colors ${
                  isActive ? 'bg-cobalt text-white' : 'text-ink-muted hover:bg-mist hover:text-ink'
                }`
              }
            >
              <svg viewBox="0 0 24 24" className="h-[18px] w-[18px] shrink-0 fill-current opacity-80">
                <path d={n.icon} />
              </svg>
              {t(`nav.${n.key}`)}
            </NavLink>
          ))}
        </nav>
        {lastOk?.finished_at ? (
          <div className="border-t border-line px-md py-3 text-[11px] text-ink-faint">
            {t('overview.lastSync')}:{' '}
            <span className="num">{fmtDateShort(lastOk.finished_at, lang, me?.numerals_pref ?? 'western')}</span>
          </div>
        ) : null}
      </aside>

      {/* main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-line bg-white px-lg py-3">
          <div />
          <div className="flex items-center gap-4">
            <button
              onClick={switchLang}
              className="en rounded-full border border-line-2 px-3 py-1 text-xs font-semibold text-ink-muted hover:border-cobalt hover:text-cobalt"
              title={lang === 'fa' ? 'Switch to English' : 'تغییر به فارسی'}
            >
              {lang === 'fa' ? 'EN' : 'فا'}
            </button>
            <span className="text-sm text-ink-muted">
              {me?.username}
              {me?.role === 'admin' ? <span className="ms-1 text-[10px] text-amber">({t('sync.admin')})</span> : null}
            </span>
            <button onClick={logout} className="text-sm font-semibold text-terracotta hover:underline">
              {t('nav.logout')}
            </button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 p-lg">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
