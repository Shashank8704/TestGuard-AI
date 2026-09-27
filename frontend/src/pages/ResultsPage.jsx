import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import AnalysisResults from '../components/AnalysisResults'
import { generateTests } from '../api/client'

export default function ResultsPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { analysis, code, tests } = location.state || {}

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Guard: if navigated directly without state, go home
  if (!analysis || !code) {
    navigate('/', { replace: true })
    return null
  }

  const handleGenerate = async () => {
    setError('')
    setLoading(true)
    try {
      const result = await generateTests(
        code,
        tests,
        analysis.missing_tests,
        analysis.edge_cases
      )
      navigate('/tests', {
        state: {
          generated: result,
          analysis,
          code,
          tests,
        },
      })
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Generation failed. Is the backend running?'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const totalIssues = analysis.missing_tests.length + analysis.edge_cases.length

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-indigo-600 rounded flex items-center justify-center text-white text-xs font-bold">TG</div>
            <button
              onClick={() => navigate('/')}
              className="text-white font-semibold tracking-tight hover:text-indigo-300 transition-colors"
            >
              TestGuard AI
            </button>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="text-slate-600">Analyze</span>
            <span className="text-slate-600">›</span>
            <span className="text-slate-300 font-medium">Results</span>
            <span className="text-slate-600">›</span>
            <span className="text-slate-600">Generate</span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto px-6 py-8 w-full">
        {/* Page heading */}
        <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
          <div>
            <h2 className="text-2xl font-bold text-white">Analysis Results</h2>
            <p className="text-sm text-slate-400 mt-1">
              {totalIssues === 0
                ? 'No significant gaps detected. Your tests look comprehensive!'
                : `${totalIssues} potential issue${totalIssues !== 1 ? 's' : ''} detected across ${analysis.functions.length} function${analysis.functions.length !== 1 ? 's' : ''}.`}
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="text-sm text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-500 
                       px-4 py-2 rounded-lg transition-colors flex-shrink-0"
          >
            ← Analyze Again
          </button>
        </div>

        {/* Results card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
          <AnalysisResults data={analysis} />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm flex items-start gap-2">
            <span className="flex-shrink-0">✕</span>
            <span>{error}</span>
          </div>
        )}

        {/* Generate button */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed 
                       text-white font-semibold px-6 py-3 rounded-lg transition-colors text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                Generating Tests…
              </>
            ) : (
              <>⚡ Generate Tests</>
            )}
          </button>
          {!loading && (
            <p className="text-xs text-slate-500">
              Will generate pytest cases for {analysis.missing_tests.length} missing scenario{analysis.missing_tests.length !== 1 ? 's' : ''} and {analysis.edge_cases.length} edge case{analysis.edge_cases.length !== 1 ? 's' : ''}.
            </p>
          )}
        </div>
      </main>
    </div>
  )
}
