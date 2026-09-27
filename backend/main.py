"""
main.py — TestGuard AI FastAPI application.

Endpoints:
  GET  /health          — Health check
  POST /analyze         — Analyze Python code for test gaps
  POST /generate-tests  — Generate pytest test cases
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    AnalyzeRequest, AnalyzeResponse,
    GenerateRequest, GenerateResponse,
    FunctionInfo, MissingTest, EdgeCase, Issue
)
from analyzer.ast_analyzer import analyze_code
from analyzer.test_analyzer import (
    parse_tests,
    count_tests,
    detect_weak_assertions,
    get_covered_function_names,
    get_covered_scenarios,
)
from analyzer.ai_layer import analyze_with_ai
from generator.test_generator import generate_with_ai, generate_fallback

app = FastAPI(title="TestGuard AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "TestGuard AI API is running.",
        "endpoints": {
            "analyze": "POST /analyze",
            "generate": "POST /generate-tests",
            "health": "GET /health",
            "docs": "GET /docs",
        }
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "TestGuard AI"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """
    Analyze Python source code and existing tests to identify gaps.

    Returns detected functions, branches, missing test scenarios,
    edge cases, risk level, and an AI-enhanced summary.
    """
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    # ── Step 1: Parse existing tests ─────────────────────────────────────────
    test_parse = parse_tests(request.tests)
    covered_functions = test_parse.get("covered_functions", set())
    covered_scenarios = get_covered_scenarios(request.tests)
    test_count_before = test_parse.get("test_count", 0)

    # ── Step 2: AST analysis ──────────────────────────────────────────────────
    ast_results = analyze_code(
        request.code,
        covered_function_names=covered_functions,
        covered_scenarios=covered_scenarios,
    )

    # ── Step 3: Weak assertion detection ────────────────────────────────────
    weak_issues = detect_weak_assertions(request.tests)

    # ── Step 4: AI enrichment ────────────────────────────────────────────────
    ai_results = analyze_with_ai(request.code, request.tests, ast_results)

    # ── Step 5: Merge results ────────────────────────────────────────────────
    all_missing = ast_results["missing_tests"] + ai_results.get("extra_missing_tests", [])
    all_edge_cases = ast_results["edge_cases"] + ai_results.get("extra_edge_cases", [])

    # Deduplicate by scenario/description
    seen_scenarios = set()
    deduped_missing = []
    for m in all_missing:
        key = m.get("scenario", "").lower().strip()
        if key not in seen_scenarios:
            seen_scenarios.add(key)
            deduped_missing.append(m)

    seen_edges = set()
    deduped_edges = []
    for e in all_edge_cases:
        key = e.get("description", "").lower().strip()
        if key not in seen_edges:
            seen_edges.add(key)
            deduped_edges.append(e)

    # ── Step 6: Build response ───────────────────────────────────────────────
    functions = [
        FunctionInfo(**f) for f in ast_results["functions"]
        if "error" not in f
    ]
    branches = ast_results["branches"]
    issues = [Issue(**i) for i in weak_issues]
    missing_tests = [MissingTest(**m) for m in deduped_missing]
    edge_cases = [EdgeCase(**e) for e in deduped_edges]

    return AnalyzeResponse(
        functions=functions,
        branches=branches,
        issues=issues,
        missing_tests=missing_tests,
        edge_cases=edge_cases,
        risk_level=ai_results.get("risk_level", ast_results["risk_level"]),
        summary=ai_results.get("summary", ast_results["summary"]),
        ai_available=ai_results.get("ai_available", False),
        test_count_before=test_count_before,
    )


@app.post("/generate-tests", response_model=GenerateResponse)
def generate_tests(request: GenerateRequest):
    """
    Generate pytest test cases for the identified missing scenarios.

    Uses AI when available, falls back to template-based generation.
    """
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    # Re-count existing tests for accurate before/after
    from analyzer.test_analyzer import count_tests as _count
    test_count_before = _count(request.tests)

    result = generate_with_ai(
        code=request.code,
        tests=request.tests,
        missing_tests=request.missing_tests,
        edge_cases=request.edge_cases,
        test_count_before=test_count_before,
    )

    return GenerateResponse(**result)
