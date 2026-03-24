import { Outlet } from 'react-router-dom'
import { SiteFooter } from '../sections/SiteFooter'
import { SiteHeader } from '../sections/SiteHeader'

export function AppLayout() {
  return (
    <div className="page-shell">
      <SiteHeader />
      <main className="app-main">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  )
}
