import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { Card, ErrorBox, PageHeader, ScorePips, SegmentBadge, Spinner } from '@/components/ui'
import { fmtDate, fmtDateShort, fmtNum, fmtToman } from '@/lib/format'
import { useContactDetail, useLabels, useMe } from '@/lib/hooks'

export default function CustomerDetail() {
  const { t } = useTranslation()
  const { contactId = '' } = useParams()
  const { data: me } = useMe()
  const detail = useContactDetail(contactId)
  const { lang, segmentLabel, segmentColor, stageLabel, meta } = useLabels()
  const numerals = me?.numerals_pref ?? 'western'

  if (detail.isLoading || !meta) return <Spinner />
  if (detail.isError || !detail.data) return <ErrorBox message={t('detail.notFound')} />

  const d = detail.data
  const latest = d.latest
  // segment rendered as an index on the best→worst scale, so the line chart
  // reads "up = healthier" at a glance
  const segIndex = new Map(meta.segments.map((s, i) => [s.code, meta.segments.length - i]))
  const chartData = d.history.map((h) => ({
    date: fmtDateShort(h.run_date, lang, 'western'),
    idx: h.segment ? segIndex.get(h.segment) ?? 0 : 0,
    segment: segmentLabel(h.segment),
  }))

  return (
    <>
      <Link to="/customers" className="mb-sm inline-block text-sm text-cobalt hover:underline">
        ← {t('detail.back')}
      </Link>
      <PageHeader
        title={d.display_name ?? d.contact_id}
        sub={
          <span className="num">
            {d.contact_id} · {d.phone ?? '—'} ·{' '}
            {d.species === 'dog' ? t('customers.speciesDog') : t('customers.speciesCat')}
          </span>
        }
      />

      {latest ? (
        <div className="grid grid-cols-2 gap-md lg:grid-cols-4">
          <Card className="p-md">
            <div className="lbl text-[10px] text-ink-faint">{t('detail.currentSegment')}</div>
            <div className="mt-2">
              <SegmentBadge label={segmentLabel(latest.segment)} color={segmentColor(latest.segment)} />
            </div>
          </Card>
          <Card className="p-md">
            <div className="lbl text-[10px] text-ink-faint">{t('detail.personaGuess')}</div>
            <div className="mt-1 text-xl font-bold">
              {latest.persona_guess}
              {latest.persona_confidence === 'confirmed' ? <span className="ms-1 text-xs text-green">✓ {t('overview.confirmed')}</span> : null}
            </div>
            <div className="text-xs text-ink-muted">{stageLabel(latest.journey_stage)}</div>
          </Card>
          <Card className="p-md">
            <div className="lbl text-[10px] text-ink-faint">{t('customers.totalAmount')}</div>
            <div className="num mt-1 text-xl font-bold text-cobalt">{fmtToman(latest.total_amount, numerals, lang)}</div>
            <div className="num text-xs text-ink-muted">
              {fmtNum(latest.order_count, numerals)} {t('customers.orders')} · {fmtNum(latest.touch_count, numerals)} {t('customers.touches')}
            </div>
          </Card>
          <Card className="p-md">
            <div className="lbl text-[10px] text-ink-faint">{t('detail.leadPillar')}</div>
            <div className="mt-1 text-sm font-semibold leading-6">{latest.lead_pillar ?? '—'}</div>
          </Card>
        </div>
      ) : null}

      <div className="mt-lg grid gap-md lg:grid-cols-2">
        <Card className="p-md">
          <h2 className="mb-sm font-bold">{t('detail.segmentTrend')}</h2>
          <div className="h-64" dir="ltr">
            <ResponsiveContainer>
              <LineChart data={chartData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
                <CartesianGrid stroke="#EDF1FB" vertical={false} />
                <XAxis dataKey="date" tickLine={false} axisLine={{ stroke: '#E5EAF6' }} />
                <YAxis
                  domain={[0, meta.segments.length]}
                  ticks={[1, Math.ceil(meta.segments.length / 2), meta.segments.length]}
                  tickFormatter={(v) => segmentLabel(meta.segments[meta.segments.length - v]?.code ?? '')}
                  width={110}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  formatter={(_, __, item) => [(item.payload as { segment: string }).segment, '']}
                  separator=""
                  contentStyle={{ borderRadius: 8, borderColor: '#E5EAF6', fontFamily: 'Vazirmatn' }}
                />
                <Line type="stepAfter" dataKey="idx" stroke="#1C48C1" strokeWidth={2.5} dot={{ r: 3, fill: '#1C48C1' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="overflow-x-auto p-0">
          <h2 className="px-md pb-sm pt-md font-bold">{t('detail.history')}</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-mist text-xs text-ink-muted">
                <th className="px-3 py-2 text-start font-semibold">{t('detail.date')}</th>
                <th className="px-3 py-2 text-start font-semibold">{t('customers.segment')}</th>
                <th className="px-3 py-2 text-start font-semibold">{t('detail.scores')}</th>
                <th className="px-3 py-2 text-start font-semibold">{t('customers.totalAmount')}</th>
              </tr>
            </thead>
            <tbody>
              {[...d.history].reverse().map((h) => (
                <tr key={h.run_date} className="border-b border-line last:border-0">
                  <td className="px-3 py-2">{fmtDate(h.run_date, lang, numerals)}</td>
                  <td className="px-3 py-2">
                    <SegmentBadge label={segmentLabel(h.segment)} color={segmentColor(h.segment)} />
                  </td>
                  <td className="num px-3 py-2">
                    {h.r_score}·{h.f_score}·{h.m_score}·{h.e_score}
                  </td>
                  <td className="num px-3 py-2">{fmtToman(h.total_amount, numerals, lang)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      {latest ? (
        <div className="mt-md">
          <Card className="flex flex-wrap items-center gap-x-xl gap-y-md p-md">
            {(
              [
                ['R', latest.r_score, '#1C48C1'],
                ['F', latest.f_score, '#2E5BE0'],
                ['M', latest.m_score, '#2F8F6B'],
                ['E', latest.e_score, '#B77E33'],
              ] as const
            ).map(([letter, score, color]) => (
              <div key={letter} className="flex items-center gap-2">
                <span className="num text-sm font-bold" style={{ color }}>{letter}</span>
                <ScorePips value={score} color={color} />
                <span className="num text-sm text-ink-muted">{score ?? '—'}</span>
              </div>
            ))}
            <div className="text-sm text-ink-muted">
              {t('detail.recency')}:{' '}
              <span className="font-semibold text-ink">
                {latest.recency_days === null
                  ? t('customers.never')
                  : t('customers.daysAgo', { n: fmtNum(latest.recency_days, numerals) })}
              </span>
            </div>
          </Card>
        </div>
      ) : null}
    </>
  )
}
