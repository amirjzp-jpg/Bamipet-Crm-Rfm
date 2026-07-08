import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'

import { Card, ErrorBox, PageHeader, SegmentBadge, Spinner } from '@/components/ui'
import { fmtDateShort, fmtNum } from '@/lib/format'
import { useLabels, useMe, useTrends } from '@/lib/hooks'

export default function Trends() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const trends = useTrends(fromDate || undefined, toDate || undefined)
  const { lang, meta, segmentLabel, segmentColor } = useLabels()
  const numerals = me?.numerals_pref ?? 'western'

  if (trends.isLoading || !meta) return <Spinner />
  if (trends.isError || !trends.data) return <ErrorBox onRetry={() => trends.refetch()} />

  const data = trends.data
  const activeSegments = meta.segments.filter((s) => data.series.some((p) => p.segment === s.code && p.count > 0))
  // pivot series into one row per run_date with a column per segment —
  // zero-filled for every active segment, since an undefined dataKey value
  // breaks recharts' stacking from that point onward
  const byDate = new Map<string, Record<string, number | string>>()
  for (const d of data.run_dates) {
    const row: Record<string, number | string> = { run_date: d, label: fmtDateShort(d, lang, 'western') }
    for (const s of activeSegments) row[s.code] = 0
    byDate.set(d, row)
  }
  for (const p of data.series) {
    const row = byDate.get(p.run_date)
    if (row) row[p.segment] = p.count
  }
  const chartData = [...byDate.values()]
  const totalMoved = data.migration.reduce((acc, m) => acc + m.count, 0)

  return (
    <>
      <PageHeader title={t('trends.title')} sub={t('trends.axisNote')} />

      <Card className="mb-md p-md">
        <h2 className="mb-sm font-bold">{t('trends.seriesTitle')}</h2>
        <div className="h-80" dir="ltr">
          <ResponsiveContainer>
            <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
              <CartesianGrid stroke="#EDF1FB" vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: '#E5EAF6' }} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ borderRadius: 8, borderColor: '#E5EAF6', fontFamily: 'Vazirmatn' }}
                formatter={(v, name) => [fmtNum(v as number, numerals), segmentLabel(name as string)]}
              />
              {activeSegments.map((s) => (
                <Area
                  key={s.code}
                  type="monotone"
                  dataKey={s.code}
                  stackId="1"
                  stroke={s.color}
                  fill={s.color}
                  fillOpacity={0.55}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-sm flex flex-wrap gap-2">
          {activeSegments.map((s) => (
            <SegmentBadge key={s.code} label={s[lang]} color={s.color} />
          ))}
        </div>
      </Card>

      <Card className="p-md">
        <div className="mb-sm flex flex-wrap items-center justify-between gap-sm">
          <h2 className="font-bold">{t('trends.migrationTitle')}</h2>
          <div className="flex items-center gap-2 text-sm">
            <label className="text-ink-muted">{t('trends.from')}</label>
            <select
              className="rounded-md border border-line-2 bg-white px-2 py-1.5 text-sm"
              value={fromDate || data.from_date || ''}
              onChange={(e) => setFromDate(e.target.value)}
            >
              {data.run_dates.map((d) => (
                <option key={d} value={d}>{fmtDateShort(d, lang, numerals)}</option>
              ))}
            </select>
            <label className="text-ink-muted">{t('trends.to')}</label>
            <select
              className="rounded-md border border-line-2 bg-white px-2 py-1.5 text-sm"
              value={toDate || data.to_date || ''}
              onChange={(e) => setToDate(e.target.value)}
            >
              {data.run_dates.map((d) => (
                <option key={d} value={d}>{fmtDateShort(d, lang, numerals)}</option>
              ))}
            </select>
          </div>
        </div>

        <p className="mb-sm text-sm text-ink-muted">
          <span className="num font-semibold text-ink">{fmtNum(totalMoved, numerals)}</span> {t('trends.moved')}
        </p>

        {data.migration.length === 0 ? (
          <p className="py-lg text-center text-ink-muted">{t('trends.noMovement')}</p>
        ) : (
          <ul className="grid gap-2 md:grid-cols-2">
            {data.migration.slice(0, 14).map((m) => (
              <li key={`${m.from_segment}->${m.to_segment}`}
                  className="flex items-center justify-between gap-2 rounded-md border border-line bg-cream px-3 py-2">
                <span className="flex min-w-0 items-center gap-2 text-sm">
                  <SegmentBadge label={segmentLabel(m.from_segment)} color={segmentColor(m.from_segment)} />
                  <span className="shrink-0 text-ink-faint">{lang === 'fa' ? '←' : '→'}</span>
                  <SegmentBadge label={segmentLabel(m.to_segment)} color={segmentColor(m.to_segment)} />
                </span>
                <span className="num shrink-0 text-sm font-bold">{fmtNum(m.count, numerals)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  )
}
