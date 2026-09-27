const COVERAGE_STATUS = {
  untested: {
    label: 'UNTESTED',
    bg: 'bg-red-900/30',
    border: 'border-red-700/60',
    text: 'text-red-300',
    title: 'No existing test calls this function.',
  },
  partial: {
    label: 'PARTIALLY TESTED',
    bg: 'bg-yellow-900/20',
    border: 'border-yellow-700/50',
    text: 'text-yellow-300',
    title: 'Existing tests exercise this function, but some branches remain untested.',
  },
  covered: {
    label: 'POTENTIALLY COVERED',
    bg: 'bg-green-900/20',
    border: 'border-green-700/50',
    text: 'text-green-300',
    title: 'Existing tests appear to exercise the detected branches.',
  },
  unknown: {
    label: 'UNKNOWN',
    bg: 'bg-slate-800',
    border: 'border-slate-600',
    text: 'text-slate-400',
    title: 'Coverage status could not be determined.',
  },
}

const RISK_CONFIG = {
  high:    { label: 'HIGH RISK',    bg: 'bg-red-900/40',    border: 'border-red-700',    text: 'text-red-300',    dot: 'bg-red-400' },
  medium:  { label: 'MEDIUM RISK',  bg: 'bg-yellow-900/40', border: 'border-yellow-700', text: 'text-yellow-300', dot: 'bg-yellow-400' },
  low:     { label: 'LOW RISK',     bg: 'bg-green-900/40',  border: 'border-green-700',  text: 'text-green-300',  dot: 'bg-green-400' },
  unknown: { label: 'UNKNOWN',      bg: 'bg-slate-800',     border: 'border-slate-600',  text: 'text-slate-400',  dot: 'bg-slate-400' },
}

const RISK_ITEM = {
  high:   { icon: '✕', color: 'text-red-400',    badge: 'bg-red-900/50 text-red-300 border-red-700' },
  medium: { icon: '⚠', color: 'text-yellow-400', badge: 'bg-yellow-900/50 text-yellow-300 border-yellow-700' },
  low:    { icon: '⚠', color: 'text-slate-400',  badge: 'bg-slate-700 text-slate-300 border-slate-600' },
}

const EDGE_ICONS = {
  boundary:      '◈',
  invalid_input: '✕',
  null:          '∅',
  overflow:      '↑',
  logic:         '⊙',
  type_error:    '⚡',
}

function RiskBadge({ level }) {
  const cfg = RISK_CONFIG[level] || RISK_CONFIG.unknown
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded border text-xs font-bold tracking-widest ${cfg.bg} ${cfg.border} ${cfg.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}

function MissingTestCard({ item }) {
  const cfg = RISK_ITEM[item.risk] || RISK_ITEM.low
  return (
    <div className="flex items-start gap-3 p-3 bg-slate-800/60 rounded border border-slate-700">
      <span className={`mt-0.5 text-base font-bold flex-shrink-0 ${cfg.color}`}>{cfg.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <span className="text-sm text-slate-200 font-medium">{item.scenario}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded border font-semibold flex-shrink-0 ${cfg.badge}`}>
            {item.risk.toUpperCase()}
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1 leading-relaxed">{item.reason}</p>
      </div>
    </div>
  )
}

function EdgeCaseCard({ item }) {
  const icon = EDGE_ICONS[item.type] || '◈'
  return (
    <div className="flex items-start gap-3 p-3 bg-slate-800/60 rounded border border-slate-700">
      <span className="mt-0.5 text-base text-indigo-400 flex-shrink-0 font-mono">{icon}</span>
      <div className="flex-1 min-w-0">
        <span className="text-sm text-slate-200">{item.description}</span>
        <span className="ml-2 text-xs text-slate-500 bg-slate-700 px-1.5 py-0.5 rounded">
          {item.type}
        </span>
      </div>
    </div>
  )
}

function Section({ title, count, children, emptyMsg }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">{title}</h3>
        {count !== undefined && (
          <span className="text-xs bg-slate-700 text-slate-400 px-2 py-0.5 rounded-full">{count}</span>
        )}
      </div>
      {count === 0 ? (
        <p className="text-sm text-slate-500 italic">{emptyMsg}</p>
      ) : children}
    </div>
  )
}

export default function AnalysisResults({ data }) {
  const { functions = [], branches = [], missing_tests = [], edge_cases = [], issues = [], risk_level, summary, ai_available } = data

  return (
    <div className="space-y-6">
      {/* Risk + Summary */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        <div className="flex-shrink-0">
          <RiskBadge level={risk_level} />
        </div>
        <div className="flex-1">
          <p className="text-sm text-slate-300 leading-relaxed">{summary}</p>
          {ai_available ? (
            <span className="mt-2 inline-flex items-center gap-1.5 text-xs text-indigo-300 bg-indigo-900/30 border border-indigo-700/50 px-2 py-1 rounded">
              ✦ AI Enhanced
            </span>
          ) : (
            <span className="mt-2 inline-flex items-center gap-1.5 text-xs text-slate-400 bg-slate-800 border border-slate-700 px-2 py-1 rounded">
              ◎ Static Analysis Only
            </span>
          )}
        </div>
      </div>

      {/* Functions */}
      <Section title="Functions Detected" count={functions.length} emptyMsg="No functions detected.">
        <div className="flex flex-col gap-2">
          {functions.map((fn, i) => {
            const status = fn.coverage_status || 'unknown'
            const cfg = COVERAGE_STATUS[status] || COVERAGE_STATUS.unknown
            return (
              <div key={i} className="flex items-center gap-3 bg-slate-800/60 border border-slate-700 rounded px-3 py-2 flex-wrap">
                <span className="text-xs text-slate-500 font-mono">def</span>
                <span className="text-sm font-mono text-indigo-300">{fn.name}</span>
                <span className="text-xs text-slate-500">({fn.args.join(', ')})</span>
                {fn.branch_count > 0 && (
                  <span className="text-xs bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded">
                    {fn.branch_count} branch{fn.branch_count !== 1 ? 'es' : ''}
                  </span>
                )}
                <span
                  title={cfg.title}
                  className={`ml-auto text-xs font-semibold px-2 py-0.5 rounded border tracking-wide cursor-default ${cfg.bg} ${cfg.border} ${cfg.text}`}
                >
                  {cfg.label}
                </span>
              </div>
            )
          })}
        </div>
      </Section>

      {/* Missing Tests */}
      <Section title="Potential Missing Tests" count={missing_tests.length} emptyMsg="No missing tests detected — coverage looks good!">
        <div className="space-y-2">
          {missing_tests.map((m, i) => <MissingTestCard key={i} item={m} />)}
        </div>
      </Section>

      {/* Edge Cases */}
      <Section title="Recommended Edge Cases" count={edge_cases.length} emptyMsg="No edge cases identified.">
        <div className="space-y-2">
          {edge_cases.map((e, i) => <EdgeCaseCard key={i} item={e} />)}
        </div>
      </Section>

      {/* Branches */}
      {branches.length > 0 && (
        <Section title="Branches Detected" count={branches.length}>
          <div className="space-y-1">
            {branches.map((b, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-slate-500 text-xs font-mono w-12 flex-shrink-0">L{b.line}</span>
                <code className="text-slate-300 bg-slate-800/60 px-2 py-0.5 rounded font-mono text-xs">{b.condition}</code>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Weak Assertions */}
      {issues.length > 0 && (
        <Section title="Test Quality Issues" count={issues.length}>
          <div className="space-y-2">
            {issues.map((iss, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-yellow-900/20 border border-yellow-800/50 rounded">
                <span className="text-yellow-400 text-sm flex-shrink-0">⚠</span>
                <p className="text-sm text-yellow-300">{iss.description}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}
