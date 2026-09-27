# TestGuard AI

> **Find what your tests missed.**

An AI-powered developer testing assistant that analyzes Python source code, identifies missing test scenarios, and generates pytest test cases.

---

## Quick Start

### 1. Backend (FastAPI)

```bash
cd testguard-ai/backend

# Create your .env file
cp env.example .env
# Edit .env and add your GEMINI_API_KEY

# Install dependencies
pip3 install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be available at: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

### 2. Frontend (React + Vite)

```bash
cd testguard-ai/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The app will be available at: http://localhost:5173

---

## Gemini API Key

The app works without a Gemini key using static AST analysis only.  
To enable AI-enhanced analysis and test generation:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create a free API key
2. Open `testguard-ai/backend/.env`
3. Add your key:
   ```
   GEMINI_API_KEY=your-key-here
   ```
4. Restart the backend server.

When AI is active, the Results page shows a **✦ AI Enhanced** badge.

---

## Demo Flow

1. Open http://localhost:5173
2. Click **"Try Example"** — fills in the discount function demo
3. Click **"⚡ Analyze Code"** — analyzes branches and edge cases
4. View the Results page: risk level, missing tests, edge cases
5. Click **"⚡ Generate Tests"** — generates pytest code
6. Use **"⎘ Copy Tests"** to copy the generated tests

---

## Architecture

```
Frontend (React + Vite + Tailwind CSS)
    ↓  POST /analyze
    ↓  POST /generate-tests
FastAPI Backend
    ├── Python AST Analyzer (stdlib ast module)
    ├── Test Analyzer (existing test parser)
    ├── AI Analysis Layer (Google Gemini gemini-flash-lite-latest)
    └── Pytest Generator (AI + template fallback)
```

---

## API Endpoints

### `POST /analyze`
```json
{
  "code": "def calculate_discount(price, age): ...",
  "tests": "def test_adult(): ..."
}
```

### `POST /generate-tests`
```json
{
  "code": "...",
  "tests": "...",
  "missing_tests": [...],
  "edge_cases": [...]
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, Tailwind CSS 3 |
| Backend | Python 3.14, FastAPI, Uvicorn |
| Analysis | Python `ast` module (stdlib) |
| AI | Google Gemini (`gemini-flash-lite-latest`) via `google-genai` SDK |
| HTTP | Axios, python-dotenv |

---

## Limitations

- Python and pytest only (MVP scope)
- No persistent storage — analysis results live in browser session
- AI analysis requires a valid Gemini API key (free tier available at AI Studio)
- Complex or very long codebases may produce verbose output
- Generated tests use placeholder imports (`from your_module import ...`) — update before running

---

*Built with IBM Bob 2.0 during a hackathon.*
