from pydantic import BaseModel
from typing import List, Optional


# ── Request Models ────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    code: str
    tests: str = ""


class GenerateRequest(BaseModel):
    code: str
    tests: str = ""
    missing_tests: List[dict] = []
    edge_cases: List[dict] = []


# ── Response Sub-Models ───────────────────────────────────────────────────────

class FunctionInfo(BaseModel):
    name: str
    args: List[str]
    has_return: bool
    line_number: int
    branch_count: int
    branches: List[str]
    coverage_status: str = "unknown"   # "untested" | "partial" | "covered" | "unknown"


class MissingTest(BaseModel):
    scenario: str
    reason: str
    risk: str          # "high" | "medium" | "low"
    function_name: str


class EdgeCase(BaseModel):
    description: str
    type: str          # "boundary" | "invalid_input" | "null" | "overflow" | "logic"
    function_name: str


class Issue(BaseModel):
    description: str
    severity: str      # "warning" | "error" | "info"
    function_name: str


# ── Response Models ───────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    functions: List[FunctionInfo]
    branches: List[dict]
    issues: List[Issue]
    missing_tests: List[MissingTest]
    edge_cases: List[EdgeCase]
    risk_level: str        # "low" | "medium" | "high" | "unknown"
    summary: str
    ai_available: bool
    test_count_before: int


class GenerateResponse(BaseModel):
    generated_tests: str
    explanation: str
    test_count_before: int
    test_count_after: int
