import { NavLink, useLocation } from 'react-router-dom'
import { Logo } from '../components/Logo'

export function SiteHeader() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  const navItems = [
    { label: 'Home', to: '/' },
    { label: 'Upload', to: '/upload' },
    { label: 'Results', to: '/results/demo' },
  ]

  return (
    <header className={`site-header ${isHome ? '' : 'site-header--app'}`.trim()}>
      <Logo as="a" href="/" />

      <nav className="site-nav" aria-label="Primary">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive ? 'is-active' : undefined)}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="site-header__actions">
        <NavLink to="/upload" className="header-link">
          Open workspace
        </NavLink>
        <NavLink to="/upload" className="button button--dark button--small">
          Upload CSV
        </NavLink>
      </div>
    </header>
  )
}
