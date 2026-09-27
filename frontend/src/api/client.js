import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

export async function analyzeCode(code, tests = '') {
  const { data } = await api.post('/analyze', { code, tests })
  return data
}

export async function generateTests(code, tests, missingTests, edgeCases) {
  const { data } = await api.post('/generate-tests', {
    code,
    tests,
    missing_tests: missingTests,
    edge_cases: edgeCases,
  })
  return data
}
