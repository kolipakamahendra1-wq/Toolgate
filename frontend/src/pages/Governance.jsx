import { useEffect, useState } from 'react'
import { RoleSwitch, useRole } from '../role.jsx'
import { getAudit, getPolicy } from '../api'

function PolicyTable({ spec }) {
  return (
    <div className="divide-y divide-line border-y border-line">
      {Object.entries(spec.tables).map(([table, g]) => (
        <div key={table} className="grid gap-2 py-4 md:grid-cols-[9rem_1fr]">
          <p className="font-mono text-sm font-medium">{table}</p>
          <div>
            <p className="flex flex-wrap gap-1.5">
              {g.columns.map((c) => (
                <span key={c} className={`rounded border px-1.5 py-0.5 font-mono text-xs ${g.masks[c] ? 'border-accent/40 bg-accent-soft text-accent' : 'border-line bg-panel'}`}>
                  {c}{g.masks[c] ? ` (${g.masks[c]})` : ''}
                </span>
              ))}
            </p>
            {g.row_filter && <p className="mt-2 font-mono text-xs text-muted">rows where {g.row_filter}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Governance() {
  const { role } = useRole()
  const [policy, setPolicy] = useState(null)
  const [audit, setAudit] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    setErr(''); setAudit(null)
    getPolicy(role.token).then(setPolicy).catch((e) => setErr(e.message === 'Failed to fetch' ? 'The API is not reachable on port 8030.' : e.message))
    getAudit(role.token).then(setAudit).catch(() => setAudit([]))
  }, [role])

  const spec = policy?.[role.id]
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 md:px-8 md:py-14">
      <h1 className="text-2xl font-semibold tracking-tight">Governance</h1>
      <p className="mt-2 max-w-[60ch] text-sm text-muted">
        The policy for each identity, defined in policy.json. Highlighted columns are masked. Tables that are missing do not exist for that identity.
      </p>
      <RoleSwitch className="mt-6 max-w-sm" />

      {err && <p className="mt-8 text-sm text-deny">{err}</p>}
      {!err && !spec && <div className="skeleton mt-8 h-32 w-full" />}
      {spec && (
        <div className="mt-8 grid gap-12 lg:grid-cols-[1fr_1fr]">
          <section>
            <h2 className="mb-1 font-medium">Grants</h2>
            <p className="mb-4 text-sm text-muted">{spec.description}</p>
            <PolicyTable spec={spec} />
          </section>
          <section className="min-w-0">
            <h2 className="mb-4 font-medium">Audit log for {role.label}</h2>
            {audit === null && <div className="skeleton h-32 w-full" />}
            {audit?.length === 0 && (
              <p className="border-y border-line py-6 text-sm text-muted">Nothing recorded for this identity. Ask a question in the playground and the calls appear here.</p>
            )}
            {audit?.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="text-muted"><tr><th className="py-2 pr-3 font-normal">time</th><th className="pr-3 font-normal">tool</th><th className="pr-3 font-normal">decision</th><th className="font-normal">detail</th></tr></thead>
                  <tbody className="divide-y divide-line border-t border-line">
                    {audit.map((a) => (
                      <tr key={a.id} className="align-top">
                        <td className="py-2 pr-3 whitespace-nowrap text-muted">{new Date(a.ts * 1000).toLocaleTimeString()}</td>
                        <td className="pr-3">{a.tool}</td>
                        <td className={`pr-3 ${a.decision === 'deny' ? 'text-deny' : a.decision === 'allow' ? 'text-accent' : 'text-muted'}`}>{a.decision}</td>
                        <td className="break-words text-muted">{a.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
