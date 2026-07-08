import { useTranslation } from 'react-i18next'
import { Cell, Pie, PieChart, Tooltip } from 'recharts'
import { Link } from 'react-router-dom'

import { Card, ErrorBox, KpiTile, PageHeader, SegmentBadge, Spinner } from '@/components/ui'
import { fmtDate, fmtNum } from '@/lib/format'
import { useLabels, useMe, useOverview, usePersonaOverview, useSyncRuns } from '@/lib/hooks'

export default function Overview() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const overview = useOverview()
  const personas = usePersonaOverview()
  const { data: runs } = useSyncRuns()
  const { lang, meta, segmentLabel, segmentColor, personaColor } = useLabels()
  const numerals = me?.numerals_pref ?? 'western'

  if (overview.isLoading || personas.isLoading || !meta) return <Spinner />
  if (overview.isError || !overview.data) return <ErrorBox onRetry={() => overview.refetch()} />

  const ov = overview.data
  const count = (code: string) => ov.segments.find((s) => s.segment === code)?.count ?? 0
  const lastOk = runs?.find((r) => r.status === 'success')
  const donutData = ov.segments.filter((s) => s.count > 0).map((s) => ({
    name: segmentLabel(s.segment),
    code: s.segment,
    value: s.count,
  }))
  const maxPersona = Math.max(1, ...(personas.data?.personas.map((p) => p.count) ?? [1]))

  return (
    <>
      <PageHeader
        title={t('overview.title')}
        sub={ov.run_date ? `${t('overview.asOf')} ${fmtDate(ov.run_date, lang, numerals)}` : undefined}
      />

      <div className="grid grid-cols-2 gap-md lg:grid-cols-4">
        <KpiTile label={t('overview.totalContacts')} value={fmtNum(ov.total_contacts, numerals)} accent="#1A1E2E" />
        <KpiTile label={t('overview.champions')} value={fmtNum(count('Champions'), numerals)} accent="#2F8F6B" />
        <KpiTile label={t('overview.atRisk')} value={fmtNum(count('At Risk') + count("Can't Lose Them"), numerals)} accent="#C1543A" />
        <KpiTile
          label={t('overview.lastSync')}
          value={lastOk?.finished_at ? fmtDate(lastOk.finished_at, lang, numerals) : '—'}
          accent="#1C48C1"
          mono={false}
          sub={lastOk ? <span className={lastOk.status === 'success' ? 'text-green' : 'text-terracotta'}>●</span> : undefined}
        />
      </div>

      <div className="mt-lg grid gap-md lg:grid-cols-2">
        {/* segment donut */}
        <Card className="p-md">
          <h2 className="mb-sm font-bold">{t('overview.segmentDist')}</h2>
          <div className="flex flex-wrap items-center gap-md">
            {/* fixed-size chart — ResponsiveContainer mismeasures inside this
                wrapping flex row, drawing the donut off-center */}
            <div className="shrink-0" dir="ltr">
              <PieChart width={230} height={230}>
                <Pie data={donutData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={95} paddingAngle={2} strokeWidth={0}>
                  {donutData.map((d) => (
                    <Cell key={d.code} fill={segmentColor(d.code)} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v) => [fmtNum(v as number, numerals), '']}
                  separator=""
                  contentStyle={{ borderRadius: 8, borderColor: '#E5EAF6', fontFamily: 'Vazirmatn' }}
                />
              </PieChart>
            </div>
            <ul className="min-w-40 flex-1 space-y-1.5">
              {ov.segments.map((s) => (
                <li key={s.segment} className="flex items-center justify-between gap-2 text-sm">
                  <Link to={`/customers?segment=${encodeURIComponent(s.segment)}`} className="hover:underline">
                    <SegmentBadge label={segmentLabel(s.segment)} color={segmentColor(s.segment)} />
                  </Link>
                  <span className="num font-semibold">{fmtNum(s.count, numerals)}</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>

        {/* persona bars */}
        <Card className="p-md">
          <h2 className="mb-sm font-bold">{t('overview.personaDist')}</h2>
          <ul className="space-y-3 pt-2">
            {personas.data?.personas.map((p) => (
              <li key={p.persona}>
                <div className="mb-1 flex items-baseline justify-between text-sm">
                  <Link to={`/customers?persona=${encodeURIComponent(p.persona)}`} className="font-semibold hover:underline">
                    {p.persona}
                    <span className="ms-2 text-[11px] font-normal text-ink-faint">
                      {meta.personas.find((m) => m.code === p.persona)?.[lang === 'fa' ? 'description_fa' : 'description_en']}
                    </span>
                  </Link>
                  <span className="text-ink-muted" dir="auto">
                    <span className="num">{fmtNum(p.count, numerals)}</span>
                    {p.confirmed > 0 ? (
                      <span className="ms-1 text-[10px] text-green">
                        (<span className="num">{fmtNum(p.confirmed, numerals)}</span> {t('overview.confirmed')})
                      </span>
                    ) : null}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-mist">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${(p.count / maxPersona) * 100}%`, backgroundColor: personaColor(p.persona) }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  )
}
