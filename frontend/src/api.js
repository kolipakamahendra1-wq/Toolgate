// Demo tokens are public and documented. Each maps to exactly one role on the server.
export const ROLES = [
  { id: 'analyst', token: 'tg-analyst', label: 'Analyst', blurb: 'Deals in EMEA and APAC. No pay data. Tickets without customers.' },
  { id: 'hr_admin', token: 'tg-hr', label: 'HR admin', blurb: 'Full employee records, personal email masked.' },
  { id: 'support', token: 'tg-support', label: 'Support', blurb: 'Tickets with customer masked. Employees by name only.' },
]

async function call(path, token, init = {}) {
  const res = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(init.headers || {}) },
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(res.status === 401 ? 'The token was rejected.' : `Request failed (${res.status}). ${body.slice(0, 160)}`)
  }
  return res.json()
}

export const chat = (token, question, useLlm) =>
  call('/api/chat', token, { method: 'POST', body: JSON.stringify({ question, use_llm: useLlm }) })
export const getPolicy = (token) => call('/api/policy', token)
export const getAudit = (token) => call('/api/audit?limit=30', token)
export const health = () => fetch('/health').then((r) => (r.ok ? r.json() : Promise.reject(new Error('down'))))
