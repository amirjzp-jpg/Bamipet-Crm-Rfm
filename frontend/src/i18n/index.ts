/** Farsi-first bilingual UI (spec §4.8: FA is the default on load; EN is
 * the toggle-to option). Language flips document.dir — full RTL mirroring,
 * not text-swap-inside-LTR. */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './en.json'
import fa from './fa.json'

const stored = localStorage.getItem('bamipet_lang') as 'fa' | 'en' | null

i18n.use(initReactI18next).init({
  resources: { fa: { translation: fa }, en: { translation: en } },
  lng: stored ?? 'fa',
  fallbackLng: 'fa',
  interpolation: { escapeValue: false },
})

export function applyLang(lang: 'fa' | 'en') {
  i18n.changeLanguage(lang)
  localStorage.setItem('bamipet_lang', lang)
  document.documentElement.lang = lang
  document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr'
  document.title = lang === 'fa' ? 'بامی‌پت · سامانهٔ تحلیل مشتریان' : 'Bamipet · Customer Analytics'
}

applyLang(stored ?? 'fa')

export default i18n
