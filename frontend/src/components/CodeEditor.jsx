export default function CodeEditor({ label, value, onChange, placeholder, rows = 12, required = false }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-300">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
        <span className="text-xs text-slate-500">{value.length} chars</span>
      </div>
      <textarea
        className="code-input w-full bg-slate-900 border border-slate-700 rounded-md p-4 text-sm text-slate-100 
                   placeholder-slate-600 resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500 
                   focus:border-transparent leading-relaxed"
        style={{ fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, monospace", minHeight: `${rows * 1.6}em` }}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        spellCheck={false}
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
      />
    </div>
  )
}
