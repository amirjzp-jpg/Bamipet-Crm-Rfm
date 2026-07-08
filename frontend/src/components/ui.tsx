/** Small branded primitives — cream ground, cobalt accents, calm spacing. */
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-md border border-line bg-white shadow-card ${className}`}>
      {children}
    </div>
  )
}

export function PageHeader({ title, sub }: { title: string; sub?: ReactNode }) {
  return (
    <header className="mb-lg">
      <h1 className="text-2xl font-extrabold text-ink md:text-3xl">{title}</h1>
      {sub ? <p className="mt-1 text-sm text-ink-muted">{sub}</p> : null}
    </header>
  )
}

export function KpiTile({ label, value, accent = '#1C48C1', sub, mono = true }: {
  label: string
  value: ReactNode
  accent?: string
  sub?: ReactNode
  /** false for mixed Farsi+digit values (dates) where forced-LTR would scramble bidi order */
  mono?: boolean
}) {
  return (
    <Card className="p-md">
      <div className="lbl text-[10px] text-ink-faint">{label}</div>
      <div className={`${mono ? 'num text-3xl' : 'text-2xl'} mt-1 font-bold`} dir={mono ? undefined : 'auto'} style={{ color: accent }}>
        {value}
      </div>
      {sub ? <div className="mt-1 text-xs text-ink-muted">{sub}</div> : null}
    </Card>
  )
}

export function SegmentBadge({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold"
      style={{ backgroundColor: `${color}18`, color }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  )
}

export function ScorePips({ value, color = '#1C48C1' }: { value: number | null; color?: string }) {
  return (
    <span className="inline-flex items-center gap-0.5" title={String(value ?? '—')}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: value !== null && i <= value ? color : '#E5EAF6' }}
        />
      ))}
    </span>
  )
}

export function Spinner() {
  const { t } = useTranslation()
  return (
    <div className="flex items-center justify-center gap-3 py-xl text-ink-muted">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-line-2 border-t-cobalt" />
      {t('common.loading')}
    </div>
  )
}

export function ErrorBox({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  const { t } = useTranslation()
  return (
    <Card className="p-lg text-center">
      <p className="text-terracotta">{message ?? t('common.error')}</p>
      {onRetry ? (
        <button onClick={onRetry} className="mt-3 rounded-md border border-line-2 px-4 py-1.5 text-sm hover:bg-mist">
          {t('common.retry')}
        </button>
      ) : null}
    </Card>
  )
}

export function Button({ children, onClick, disabled, variant = 'primary', type = 'button' }: {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'ghost' | 'danger'
  type?: 'button' | 'submit'
}) {
  const styles = {
    primary: 'bg-cobalt text-white hover:bg-cobalt-soft disabled:bg-line-2',
    ghost: 'border border-line-2 text-ink hover:bg-mist disabled:text-ink-faint',
    danger: 'border border-terracotta/40 text-terracotta hover:bg-terracotta/5',
  }[variant]
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      className={`rounded-md px-4 py-2 text-sm font-semibold transition-colors ${styles}`}>
      {children}
    </button>
  )
}

export function Select({ value, onChange, options, allLabel }: {
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  allLabel: string
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-md border border-line-2 bg-white px-3 py-2 text-sm focus:border-cobalt focus:outline-none"
    >
      <option value="">{allLabel}</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  )
}
