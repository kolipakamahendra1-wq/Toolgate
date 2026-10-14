import { createContext, useContext, useState } from 'react'
import { ROLES } from './api'

const RoleCtx = createContext(null)

export function RoleProvider({ children }) {
  const [role, setRole] = useState(ROLES[0])
  return <RoleCtx.Provider value={{ role, setRole }}>{children}</RoleCtx.Provider>
}

export const useRole = () => useContext(RoleCtx)

export function RoleSwitch({ className = '' }) {
  const { role, setRole } = useRole()
  return (
    <div role="radiogroup" aria-label="Identity" className={`grid grid-cols-3 rounded-md border border-line bg-panel p-1 ${className}`}>
      {ROLES.map((r) => (
        <button
          key={r.id}
          role="radio"
          aria-checked={role.id === r.id}
          onClick={() => setRole(r)}
          className={`btn rounded px-3 py-1.5 text-sm font-medium ${role.id === r.id ? 'bg-ink text-white' : 'text-muted hover:text-ink'}`}
        >
          {r.label}
        </button>
      ))}
    </div>
  )
}
