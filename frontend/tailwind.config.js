/** Bamipet brand tokens — lifted verbatim from bamipet-visual-guidelines.md
 * and the validated CSS in bamipet-1-foundation.html. Do not add colors
 * outside this system; the terracotta "danger" is the spec §4.7 extension. */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        cobalt: { DEFAULT: '#1C48C1', deep: '#123086', soft: '#2E5BE0' },
        ink: { DEFAULT: '#1A1E2E', muted: '#616A7D', faint: '#8B93A5' },
        cream: { DEFAULT: '#FAF9F6', 2: '#F4F2EC' },
        amber: { DEFAULT: '#B77E33', deep: '#8A5D1F', bg: '#FBF5EA', line: '#EAD9B8' },
        green: { DEFAULT: '#2F8F6B' },
        terracotta: { DEFAULT: '#C1543A' },
        line: { DEFAULT: '#E5EAF6', 2: '#D6DEF1' },
        mist: { DEFAULT: '#F4F6FC', 2: '#EDF1FB' },
      },
      fontFamily: {
        fa: ['Vazirmatn', 'sans-serif'],
        en: ['Inter', 'sans-serif'],
      },
      borderRadius: { sm: '4px', md: '8px' },
      spacing: { xs: '4px', sm: '8px', md: '16px', lg: '32px', xl: '64px' },
      boxShadow: {
        // the exact card shadow from the brand HTML docs
        card: '0 1px 2px rgba(18,48,134,.05), 0 20px 40px -24px rgba(18,48,134,.18)',
        sheet: '0 1px 2px rgba(18,48,134,.05), 0 40px 80px -40px rgba(18,48,134,.22)',
      },
    },
  },
  plugins: [],
}
