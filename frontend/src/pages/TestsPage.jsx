import { useNavigate, useLocation } from 'react-router-dom'
import GeneratedTests from '../components/GeneratedTests'

export default function TestsPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { generated, analysis, code, tests } = location.state || {}

  // Guard
  if (!generated || !code) {
    navigate('/', { replace: true })
    return null
  }

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
            <span className="text-slate-600">Results</span>
            <span className="text-slate-600">›</span>
            <span className="text-slate-300 font-medium">Generated Tests</span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto px-6 py-8 w-full">
        {/* Page heading */}
        <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
          <div>
            <h2 className="text-2xl font-bold text-white">Generated Tests</h2>
            <p className="text-sm text-slate-400 mt-1">
              AI-generated recommendations — review and adapt before adding to your project.
            </p>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <button
              onClick={() => navigate('/results', { state: { analysis, code, tests } })}
              className="text-sm text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-500 
                         px-4 py-2 rounded-lg transition-colors"
            >
              ← Back to Analysis
            </button>
            <button
              onClick={() => navigate('/')}
              className="text-sm text-slate-500 hover:text-slate-400 transition-colors"
            >
              Start Over
            </button>
          </div>
        </div>

        {/* Generated tests component */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <GeneratedTests
            code={generated.generated_tests}
            explanation={generated.explanation}
            testCountBefore={generated.test_count_before}
            testCountAfter={generated.test_count_after}
          />
        </div>

        {/* Disclaimer */}
        <p className="mt-4 text-xs text-slate-600 leading-relaxed">
          ⓘ These are AI-generated test recommendations. TestGuard AI does not guarantee complete coverage or the absence of bugs. 
          Always review generated tests for correctness before committing them to your codebase.
        </p>
      </main>
    </div>
  )
}
