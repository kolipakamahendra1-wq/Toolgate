import { useEffect, useRef, useState } from 'react'
import { PaperPlaneTilt, ProhibitInset, CheckCircle, WarningCircle } from '@phosphor-icons/react'
import { RoleSwitch, useRole } from '../role.jsx'
import { chat } from '../api'

const EXAMPLES = [
  'List all salaries',
  'What is our pipeline by region and stage?',
  'Headcount by department',
  'Show me ticket 101',
  'Users loop on the SSO login page, what do I check?',
  'What are the compensation bands for engineers?',
]

function Trace({ steps }) {
  return (
    <ol className="divide-y divide-line border-y border-line font-mono text-xs">
      {steps.map((s, i) => {
        const bad = s.step === 'act' && !s.ok
        return (
          <li key={i} className="grid grid-cols-[4.5rem_1fr] gap-3 py-2.5">
            <span className={bad ? 'text-deny' : 'text-accent'}>{s.step}</span>
            <span className="break-words text-muted">
              {s.step === 'discover' && `${s.tools.length} tools: ${s.tools.join(', ')}`}
              {s.step === 'plan' && `${s.source}: ${s.tool} ${JSON.stringify(s.args)}`}
              {s.step === 'act' && `${s.tool} ${s.ok ? 'ok' : s.denied ? 'denied' : 'error'}`}
              {s.step === 'reflect' && s.note}
              {s.step === 'answer' && `written by ${s.source}`}
            </span>
          </li>
        )
      })}
    </ol>
  )
}

function Skeleton({ seconds, llm }) {
  return (
    <div aria-busy="true" aria-live="polite">
      <div className="skeleton h-5 w-3/5" />
      <div className="skeleton mt-3 h-4 w-full" />
      <div className="skeleton mt-2 h-4 w-4/5" />
      <p className="mt-5 font-mono text-xs text-muted">
        {llm ? `Waiting for the local model, ${seconds}s. Expect up to a minute on CPU.` : `Running, ${seconds}s`}
      </p>
    </div>
  )
}

export default function Playground() {
  const { role } = useRole()
  const [q, setQ] = useState(EXAMPLES[0])
  const [useLlm, setUseLlm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [secs, setSecs] = useState(0)
  const [out, setOut] = useState(null)
  const [err, setErr] = useState('')
  const timer = useRef(null)

  useEffect(() => () => clearInterval(timer.current), [])
  useEffect(() => { setOut(null); setErr('') }, [role])

  async function ask(e) {
    e?.preventDefault()
    if (!q.trim() || busy) return
    setBusy(true); setErr(''); setOut(null); setSecs(0)
    timer.current = setInterval(() => setSecs((s) => s + 1), 1000)
    try {
      setOut(await chat(role.token, q.trim(), useLlm))
    } catch (x) {
      setErr(x.message === 'Failed to fetch' ? 'The API is not reachable. Start it with: uvicorn app.main:create_default --factory --port 8030' : x.message)
    } finally {
      clearInterval(timer.current); setBusy(false)
    }
  }

  return (
    <div className="mx-auto grid max-w-7xl gap-10 px-4 py-10 md:grid-cols-[22rem_1fr] md:px-8 md:py-14">
      <aside className="grid content-start gap-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Playground</h1>
          <p className="mt-2 text-sm text-muted">Pick who is asking, then ask. The identity is set by the token, not by the question.</p>
        </div>
        <div>
          <p className="mb-2 text-sm font-medium">Identity</p>
          <RoleSwitch />
          <p className="mt-2 text-sm text-muted">{role.blurb}</p>
        </div>
        <div>
          <p className="mb-2 text-sm font-medium">Examples</p>
          <ul className="divide-y divide-line border-y border-line">
            {EXAMPLES.map((x) => (
              <li key={x}>
                <button onClick={() => setQ(x)} className="w-full py-2 text-left text-sm text-muted hover:text-ink">{x}</button>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      <section className="min-w-0">
        <form onSubmit={ask} className="grid gap-3">
          <label htmlFor="q" className="text-sm font-medium">Question</label>
          <textarea
            id="q" rows={3} value={q} onChange={(e) => setQ(e.target.value)} maxLength={1000}
            className="w-full rounded-md border border-line bg-panel p-3 text-sm focus:border-accent"
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} className="size-4 accent-[#0d7a6b]" />
              Use the local model (qwen2.5:3b)
            </label>
            <button disabled={busy || !q.trim()} className="btn inline-flex items-center gap-2 rounded-md bg-ink px-5 py-2.5 text-sm font-medium text-white hover:bg-accent disabled:opacity-50">
              <PaperPlaneTilt size={16} weight="bold" /> {busy ? 'Asking' : 'Ask as ' + role.label}
            </button>
          </div>
          <p className="text-xs text-muted">{useLlm ? 'The model plans the tool call and writes the answer. Slow on CPU.' : 'Rule router, no model. Instant, and the same policy applies.'}</p>
        </form>

        <div className="mt-8 min-h-48 rounded-lg border border-line bg-panel p-5" aria-live="polite">
          {busy && <Skeleton seconds={secs} llm={useLlm} />}
          {!busy && err && (
            <p className="flex gap-2 text-sm text-deny"><WarningCircle size={20} className="shrink-0" /> {err}</p>
          )}
          {!busy && !err && !out && (
            <div className="text-sm text-muted">
              <p className="font-medium text-ink">No answer yet</p>
              <p className="mt-1 max-w-[50ch]">Run "List all salaries" as Analyst, then switch to HR admin and run it again.</p>
            </div>
          )}
          {!busy && out && (
            <div>
              <p className={`flex items-center gap-2 text-sm font-medium ${out.denied ? 'text-deny' : 'text-accent'}`}>
                {out.denied ? <ProhibitInset size={18} weight="bold" /> : <CheckCircle size={18} weight="bold" />}
                {out.denied ? 'Denied by policy' : `Answered with ${out.tool}`}
              </p>
              <pre className="mt-3 whitespace-pre-wrap break-words font-mono text-sm leading-relaxed">{out.answer}</pre>
              <div className="mt-6">
                <p className="mb-2 text-sm font-medium">Agent trace</p>
                <Trace steps={out.trace} />
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
