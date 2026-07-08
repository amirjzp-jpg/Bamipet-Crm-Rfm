import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Route, BrowserRouter, Routes } from 'react-router-dom'
import { useEffect } from 'react'

import Layout from '@/components/Layout'
import { getTokens } from '@/lib/api'
import { useMe } from '@/lib/hooks'
import { applyLang } from '@/i18n'
import Admin from '@/pages/Admin'
import CustomerDetail from '@/pages/CustomerDetail'
import Customers from '@/pages/Customers'
import Login from '@/pages/Login'
import Overview from '@/pages/Overview'
import Settings from '@/pages/Settings'
import Trends from '@/pages/Trends'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
})

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!getTokens()) return <Navigate to="/login" replace />
  return <>{children}</>
}

/** Apply the user's stored language preference once their profile loads
 * (localStorage covers the pre-login flash; the server pref wins after). */
function LangSync() {
  const { data: me } = useMe()
  useEffect(() => {
    if (me && me.language_pref !== (localStorage.getItem('bamipet_lang') ?? 'fa')) {
      applyLang(me.language_pref)
    }
  }, [me])
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            element={
              <RequireAuth>
                <LangSync />
                <Layout />
              </RequireAuth>
            }
          >
            <Route path="/" element={<Overview />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/customers/:contactId" element={<CustomerDetail />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/sync" element={<Admin />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
