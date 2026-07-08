/** Number/date display rules from spec §4.4–4.5:
 *  - Western numerals default even in FA mode; Persian numerals are a
 *    per-user preference toggle.
 *  - Dates display Jalali in FA mode, Gregorian in EN mode; storage is ISO.
 *  - Money is Toman with thousands separators, internal-tool-visible. */
import { formatJalali, formatJalaliShort } from './jalali'

export type Numerals = 'western' | 'persian'
export type Lang = 'fa' | 'en'

const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'

export function toPersianDigits(s: string): string {
  return s.replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)])
}

export function fmtNum(n: number | null | undefined, numerals: Numerals): string {
  if (n === null || n === undefined) return '—'
  const s = new Intl.NumberFormat('en-US').format(n)
  return numerals === 'persian' ? toPersianDigits(s) : s
}

export function fmtToman(n: number | null | undefined, numerals: Numerals, lang: Lang): string {
  if (n === null || n === undefined) return '—'
  const s = fmtNum(n, numerals)
  return lang === 'fa' ? `${s} تومان` : `${s} T`
}

export function fmtDate(iso: string | null | undefined, lang: Lang, numerals: Numerals): string {
  if (!iso) return '—'
  const s = lang === 'fa' ? formatJalali(iso) : new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  return numerals === 'persian' ? toPersianDigits(s) : s
}

export function fmtDateShort(iso: string | null | undefined, lang: Lang, numerals: Numerals): string {
  if (!iso) return '—'
  const s = lang === 'fa' ? formatJalaliShort(iso) : new Date(iso).toLocaleDateString('en-GB')
  return numerals === 'persian' ? toPersianDigits(s) : s
}
