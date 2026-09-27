import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CodeEditor from '../components/CodeEditor'
import { analyzeCode } from '../api/client'
import { EXAMPLE_CODE, EXAMPLE_TESTS } from '../api/examples'

export default function HomePage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [tests, setTests] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleExample = () => {
    setCode(EXAMPLE_CODE)
    setTests(EXAMPLE_TESTS)
    setError('')
  }

  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please paste some Python code before analyzing.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const result = await analyzeCode(code, tests)
      navigate('/results', { state: { analysis: result, code, tests } })
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Analysis failed. Is the backend running?'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-indigo-600 rounded flex items-center justify-center text-white text-xs font-bold">TG</div>
            <span className="text-white font-semibold tracking-tight">TestGuard AI</span>
          </div>
          <span className="text-xs text-slate-500 hidden sm:block">Python · pytest · AI-powered</span>
        </div>
      </header>

      {/* Hero */}
      <div className="max-w-5xl mx-auto px-6 pt-12 pb-8 w-full">
        <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
          Find what your tests missed.
        </h1>
        <p className="mt-3 text-slate-400 text-base leading-relaxed max-w-2xl">
          Paste your Python code and existing pytest tests. TestGuard AI analyzes your code with static analysis 
          and AI to surface untested branches, boundary conditions, and edge cases — then generates the missing tests.
        </p>
      </div>

      {/* Main form */}
      <main className="flex-1 max-w-5xl mx-auto px-6 pb-12 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <CodeEditor
              label="Python Source Code"
              value={code}
              onChange={setCode}
              placeholder={'def calculate_discount(price, age):\n    if age < 18:\n        return price * 0.5\n    return price'}
              rows={14}
              required
            />
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <CodeEditor
              label="Existing Tests (optional)"
              value={tests}
              onChange={setTests}
              placeholder={'def test_adult():\n    assert calculate_discount(100, 20) == 100\n\n# Paste your existing pytest tests here\n# or leave empty to analyze from scratch'}
              rows={14}
            />
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm flex items-start gap-2">
            <span className="flex-shrink-0">✕</span>
            <span>{error}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed 
                       text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                Analyzing…
              </>
            ) : (
              <>⚡ Analyze Code</>
            )}
          </button>

          <button
            onClick={handleExample}
            disabled={loading}
            className="text-sm text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-500 
                       px-4 py-2.5 rounded-lg transition-colors"
          >
            Try Example
          </button>

          {(code || tests) && !loading && (
            <button
              onClick={() => { setCode(''); setTests(''); setError('') }}
              className="text-sm text-slate-500 hover:text-slate-400 transition-colors ml-auto"
            >
              Clear
            </button>
          )}
        </div>

        {/* Feature hints */}
        <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { icon: '⊙', title: 'Branch Analysis', desc: 'Detects untested if/elif/else paths using Python AST.' },
            { icon: '◈', title: 'Boundary Detection', desc: 'Surfaces off-by-one and numeric boundary conditions.' },
            { icon: '✦', title: 'AI Recommendations', desc: 'GPT-4o-mini identifies logic gaps beyond static analysis.' },
          ].map(f => (
            <div key={f.title} className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
              <div className="text-indigo-400 text-lg mb-2">{f.icon}</div>
              <div className="text-sm font-medium text-slate-300 mb-1">{f.title}</div>
              <div className="text-xs text-slate-500 leading-relaxed">{f.desc}</div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
