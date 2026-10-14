import { useEffect, useState } from 'react'
import { NavLink, Link, Route, Routes, useLocation } from 'react-router-dom'
import { GithubLogo, List, X } from '@phosphor-icons/react'
import { RoleProvider } from './role.jsx'
import { health } from './api'
import Landing from './pages/Landing.jsx'
import Playground from './pages/Playground.jsx'
import Governance from './pages/Governance.jsx'
import Docs from './pages/Docs.jsx'

const LINKS = [
  ['/playground', 'Playground'],
  ['/governance', 'Governance'],
  ['/docs', 'Docs'],
]

function ScrollTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

function Nav() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  useEffect(() => setOpen(false), [pathname])
  const cls = ({ isActive }) => `text-sm ${isActive ? 'text-ink font-medium' : 'text-muted hover:text-ink'}`
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 md:px-8">
        <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="grid size-6 place-items-center rounded-md bg-ink font-mono text-xs text-white">T</span>
          Toolgate
        </Link>
        <nav className="hidden items-center gap-7 md:flex" aria-label="Main">
          {LINKS.map(([to, label]) => <NavLink key={to} to={to} className={cls}>{label}</NavLink>)}
          <a href="https://github.com/kolipakamahendra1-wq" target="_blank" rel="noreferrer" className="text-muted hover:text-ink" aria-label="GitHub">
            <GithubLogo size={20} />
          </a>
        </nav>
        <button className="md:hidden" aria-label="Menu" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? <X size={22} /> : <List size={22} />}
        </button>
      </div>
      {open && (
        <nav className="grid gap-1 border-t border-line px-4 py-3 md:hidden" aria-label="Mobile">
          {LINKS.map(([to, label]) => <NavLink key={to} to={to} className={`${cls({ isActive: pathname === to })} py-2`}>{label}</NavLink>)}
        </nav>
      )}
    </header>
  )
}

function Footer() {
  const [h, setH] = useState(null)
  useEffect(() => { health().then(setH).catch(() => setH(false)) }, [])
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 md:grid-cols-[2fr_1fr_1fr] md:px-8">
        <div>
          <p className="font-semibold tracking-tight">Toolgate</p>
          <p className="mt-2 max-w-sm text-sm text-muted">A portfolio build: MCP tools, role-scoped data access and a LangGraph agent, running on a local model.</p>
        </div>
        <div className="grid content-start gap-2 text-sm">
          <Link className="text-muted hover:text-ink" to="/playground">Playground</Link>
          <Link className="text-muted hover:text-ink" to="/governance">Governance</Link>
          <Link className="text-muted hover:text-ink" to="/docs">Docs</Link>
        </div>
        <div className="text-sm">
          <p className="flex items-center gap-2 text-muted">
            <span className={`size-2 rounded-full ${h ? 'bg-accent' : h === false ? 'bg-deny' : 'bg-line'}`} />
            {h ? `API up, ${h.model}` : h === false ? 'API unreachable' : 'Checking API'}
          </p>
          <p className="mt-2 text-muted">Built by Mahendra</p>
        </div>
      </div>
    </footer>
  )
}

export default function App() {
  return (
    <RoleProvider>
      <ScrollTop />
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/governance" element={<Governance />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </main>
      <Footer />
    </RoleProvider>
  )
}
