const TOOLS = [
  ['list_tables', 'Tables and columns this identity may see.'],
  ['run_sql', 'One read-only SELECT, rewritten to the identity\'s scope.'],
  ['search_docs', 'Vector search over documents the identity may read.'],
  ['get_ticket', 'One support ticket by id, through the same governed path.'],
]

const API = [
  ['GET', '/health', 'Status, model and embedding provider. No token.'],
  ['GET', '/api/me', 'Role and grants for the token.'],
  ['GET', '/api/policy', 'Grants for the token\'s own role.'],
  ['GET', '/api/audit', 'Recent audit entries for the token\'s role.'],
  ['POST', '/api/chat', 'Run the agent. Body: question, use_llm.'],
]

const MAP = [
  ['Unity Catalog grants', 'policy.json with column grants, row filters and masks, enforced by SQL rewriting'],
  ['Vector Search', 'SQLite plus numpy cosine search, role ACL applied before ranking'],
  ['Genie', 'The model writes SQL; a parser-based guard validates and scopes it'],
  ['Databricks Agent Framework', 'LangGraph graph with an MCP client'],
]

const Section = ({ id, title, children }) => (
  <section id={id} className="scroll-mt-20 border-t border-line py-10 first:border-0">
    <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
    <div className="mt-4 max-w-[70ch] space-y-3 text-sm leading-relaxed text-muted">{children}</div>
  </section>
)

const Rows = ({ rows }) => (
  <dl className="divide-y divide-line border-y border-line">
    {rows.map(([a, b, c]) => (
      <div key={a + b} className="grid gap-1 py-3 md:grid-cols-[11rem_1fr]">
        <dt className="font-mono text-xs text-ink">{c ? `${a} ${b}` : a}</dt>
        <dd>{c || b}</dd>
      </div>
    ))}
  </dl>
)

export default function Docs() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 md:px-8 md:py-14">
      <h1 className="text-2xl font-semibold tracking-tight">Docs</h1>

      <Section id="design" title="Design">
        <p>An agent proposes tool calls. A fresh MCP server process, started with a fixed role, executes them. The agent graph runs discover, plan, act, an optional single retry on malformed SQL, then answer.</p>
        <p>Denials are never retried. A retry cannot widen access, but repeated probing is noise in the audit log.</p>
      </Section>
      <Section id="tools" title="MCP tools"><Rows rows={TOOLS} /></Section>
      <Section id="api" title="HTTP API"><Rows rows={API} /></Section>
      <Section id="mapping" title="Relation to Databricks">
        <p>This project is inspired by an enterprise pattern built on Databricks. It runs entirely locally and does not use Databricks. These are the local equivalents:</p>
        <Rows rows={MAP} />
      </Section>
      <Section id="limits" title="Limits">
        <p>Demo tokens are public. A real deployment needs real identity, such as OIDC, and a database with native row-level security.</p>
        <p>The SQL guard covers SQLite syntax. Another dialect needs its own tests. The 3B model plans simple queries well and misses joins, which is why the rule router exists.</p>
        <p>Docker images and CI were written but not run in the authoring environment.</p>
      </Section>
    </div>
  )
}
