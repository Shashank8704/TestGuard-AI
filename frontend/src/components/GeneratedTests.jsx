import { useState } from 'react'

export default function GeneratedTests({ code, explanation, testCountBefore, testCountAfter }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback for browsers without clipboard API
      const el = document.createElement('textarea')
      el.value = code
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="space-y-4">
      {/* Before/After summary */}
      <div className="flex items-center gap-4 p-4 bg-slate-800/60 border border-slate-700 rounded-lg">
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-400">{testCountBefore}</div>
          <div className="text-xs text-slate-500 mt-0.5">existing test{testCountBefore !== 1 ? 's' : ''}</div>
        </div>
        <div className="text-slate-500 text-xl">→</div>
        <div className="text-center">
          <div className="text-2xl font-bold text-indigo-400">{testCountAfter}</div>
          <div className="text-xs text-slate-500 mt-0.5">recommended test{testCountAfter !== 1 ? 's' : ''}</div>
        </div>
        <div className="flex-1 ml-2">
          <p className="text-sm text-slate-300 leading-relaxed">{explanation}</p>
        </div>
      </div>

      {/* Code block */}
      <div className="relative">
        <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border border-slate-700 border-b-slate-900 rounded-t-lg">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500/70" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <span className="w-3 h-3 rounded-full bg-green-500/70" />
            <span className="ml-2 text-xs text-slate-500">generated_tests.py</span>
          </div>
          <button
            onClick={handleCopy}
            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded border transition-all ${
              copied
                ? 'bg-green-900/40 border-green-700 text-green-300'
                : 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600 hover:text-white'
            }`}
          >
            {copied ? '✓ Copied!' : '⎘ Copy Tests'}
          </button>
        </div>
        <pre className="overflow-auto p-4 bg-slate-950 border border-t-0 border-slate-700 rounded-b-lg text-sm text-slate-200 leading-relaxed"
             style={{ fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, monospace", maxHeight: '520px' }}>
          <code>{code}</code>
        </pre>
      </div>
    </div>
  )
}
