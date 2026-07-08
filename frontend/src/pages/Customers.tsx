import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Button, Card, ErrorBox, PageHeader, ScorePips, SegmentBadge, Select, Spinner } from '@/components/ui'
import { downloadFile } from '@/lib/api'
import { fmtNum, fmtToman } from '@/lib/format'
import { useContacts, useLabels, useMe } from '@/lib/hooks'

const SORTABLE: Record<string, string> = {
  total_amount: 'customers.totalAmount',
  order_count: 'customers.orders',
  recency_days: 'customers.lastOrder',
  touch_count: 'customers.touches',
}

export default function Customers() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const [params, setParams] = useSearchParams()
  const [searchInput, setSearchInput] = useState(params.get('search') ?? '')
  const { lang, meta, segmentLabel, segmentColor, stageLabel } = useLabels()
  const numerals = me?.numerals_pref ?? 'western'

  const segment = params.get('segment') ?? ''
  const persona = params.get('persona') ?? ''
  const journeyStage = params.get('journey_stage') ?? ''
  const search = params.get('search') ?? ''
  const sort = params.get('sort') ?? 'total_amount'
  const order = params.get('order') ?? 'desc'
  const page = Number(params.get('page') ?? '1')
  const pageSize = 25

  const contacts = useContacts({
    segment, persona, journey_stage: journeyStage, search, sort, order, page, page_size: pageSize,
  })

  function setParam(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next, { replace: true })
  }

  function toggleSort(col: string) {
    if (sort === col) setParam('order', order === 'desc' ? 'asc' : 'desc')
    else {
      setParam('sort', col)
      setParam('order', 'desc')
    }
  }

  function exportCsv() {
    const qs = new URLSearchParams()
    if (segment) qs.set('segment', segment)
    if (persona) qs.set('persona', persona)
    if (journeyStage) qs.set('journey_stage', journeyStage)
    if (search) qs.set('search', search)
    downloadFile(`/export/contacts.csv?${qs.toString()}`, 'bamipet-contacts.csv')
  }

  const totalPages = contacts.data ? Math.max(1, Math.ceil(contacts.data.total / pageSize)) : 1

  return (
    <>
      <PageHeader title={t('customers.title')} />

      {/* filter bar */}
      <Card className="mb-md flex flex-wrap items-center gap-sm p-sm">
        <form
          className="min-w-52 flex-1"
          onSubmit={(e) => {
            e.preventDefault()
            setParam('search', searchInput)
          }}
        >
          <input
            className="w-full rounded-md border border-line-2 px-3 py-2 text-sm focus:border-cobalt focus:outline-none"
            placeholder={t('customers.search')}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </form>
        <Select value={segment} onChange={(v) => setParam('segment', v)} allLabel={`${t('customers.segment')}: ${t('customers.all')}`}
          options={(meta?.segments ?? []).map((s) => ({ value: s.code, label: s[lang] }))} />
        <Select value={persona} onChange={(v) => setParam('persona', v)} allLabel={`${t('customers.persona')}: ${t('customers.all')}`}
          options={(meta?.personas ?? []).map((p) => ({ value: p.code, label: p.code }))} />
        <Select value={journeyStage} onChange={(v) => setParam('journey_stage', v)} allLabel={`${t('customers.journeyStage')}: ${t('customers.all')}`}
          options={(meta?.journey_stages ?? []).map((s) => ({ value: s.code, label: s[lang] }))} />
        <Button variant="ghost" onClick={exportCsv}>{t('customers.export')}</Button>
      </Card>

      {contacts.isLoading ? <Spinner /> : null}
      {contacts.isError ? <ErrorBox onRetry={() => contacts.refetch()} /> : null}

      {contacts.data ? (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-mist text-start text-xs text-ink-muted">
                <th className="px-3 py-2.5 text-start font-semibold">{t('customers.name')}</th>
                <th className="px-3 py-2.5 text-start font-semibold">{t('customers.segment')}</th>
                <th className="px-3 py-2.5 text-start font-semibold">{t('customers.persona')}</th>
                <th className="px-3 py-2.5 text-start font-semibold">R·F·M·E</th>
                {Object.entries(SORTABLE).map(([col, label]) => (
                  <th key={col} className="cursor-pointer px-3 py-2.5 text-start font-semibold hover:text-cobalt" onClick={() => toggleSort(col)}>
                    {t(label)}
                    {sort === col ? <span className="num ms-1">{order === 'desc' ? '↓' : '↑'}</span> : null}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contacts.data.items.map((c) => (
                <tr key={c.contact_id} className="border-b border-line last:border-0 hover:bg-mist/60">
                  <td className="px-3 py-2.5">
                    <Link to={`/customers/${c.contact_id}`} className="font-semibold text-cobalt hover:underline" dir="auto">
                      {c.display_name ?? c.contact_id}
                    </Link>
                    <div className="num text-[11px] text-ink-faint">
                      {c.phone} · {c.species === 'dog' ? t('customers.speciesDog') : t('customers.speciesCat')}
                    </div>
                  </td>
                  <td className="px-3 py-2.5">
                    <SegmentBadge label={segmentLabel(c.segment)} color={segmentColor(c.segment)} />
                  </td>
                  <td className="px-3 py-2.5">
                    {c.persona_guess}
                    {c.persona_confidence === 'confirmed' ? <span className="ms-1 text-[10px] text-green">✓</span> : null}
                    <div className="text-[11px] text-ink-faint">{stageLabel(c.journey_stage)}</div>
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex flex-col gap-0.5">
                      <ScorePips value={c.r_score} color="#1C48C1" />
                      <ScorePips value={c.f_score} color="#2E5BE0" />
                      <ScorePips value={c.m_score} color="#2F8F6B" />
                      <ScorePips value={c.e_score} color="#B77E33" />
                    </div>
                  </td>
                  <td className="num px-3 py-2.5">{fmtToman(c.total_amount, numerals, lang)}</td>
                  <td className="num px-3 py-2.5">{fmtNum(c.order_count, numerals)}</td>
                  <td className="px-3 py-2.5">
                    {c.recency_days === null ? t('customers.never') : t('customers.daysAgo', { n: fmtNum(c.recency_days, numerals) })}
                  </td>
                  <td className="num px-3 py-2.5">{fmtNum(c.touch_count, numerals)}</td>
                </tr>
              ))}
              {contacts.data.items.length === 0 ? (
                <tr><td colSpan={8} className="px-3 py-xl text-center text-ink-muted">{t('customers.empty')}</td></tr>
              ) : null}
            </tbody>
          </table>

          {/* pagination */}
          <div className="flex items-center justify-between border-t border-line px-3 py-2 text-sm text-ink-muted">
            <span className="num">
              {fmtNum(contacts.data.total, numerals)} {t('overview.contactsUnit')}
            </span>
            <div className="flex items-center gap-2">
              <Button variant="ghost" disabled={page <= 1} onClick={() => setParam('page', String(page - 1))}>
                {t('customers.prev')}
              </Button>
              <span className="num">{fmtNum(page, numerals)} {t('customers.of')} {fmtNum(totalPages, numerals)}</span>
              <Button variant="ghost" disabled={page >= totalPages} onClick={() => setParam('page', String(page + 1))}>
                {t('customers.next')}
              </Button>
            </div>
          </div>
        </Card>
      ) : null}
    </>
  )
}
