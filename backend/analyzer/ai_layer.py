"""
ai_layer.py — Google Gemini integration for enhanced code analysis.

Enriches AST analysis results with AI-detected:
- Additional missing test scenarios
- Additional edge cases
- Risk level assessment
- Human-readable summary

Degrades gracefully: if the API call fails for any reason,
returns ai_available=False and the caller uses AST-only results.
"""

import os
import json

from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

_GEMINI_AVAILABLE = False
_client = None

try:
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key not in ("your-gemini-api-key-here", "your-openai-api-key-here"):
        _client = genai.Client(api_key=api_key)
        _GEMINI_AVAILABLE = True
except Exception:
    pass


def _build_analysis_prompt(code: str, tests: str, ast_results: dict) -> str:
    """Build the prompt for the AI analysis call."""
    func_names = [f.get("name", "?") for f in ast_results.get("functions", [])]
    branch_conditions = [b.get("condition", "") for b in ast_results.get("branches", [])]
    ast_missing = [m.get("scenario", "") for m in ast_results.get("missing_tests", [])]

    prompt = f"""You are a Python testing expert helping developers improve test coverage.

Analyze the following Python code and existing tests, then identify ADDITIONAL missing test scenarios beyond those already detected.

## Python Source Code
```python
{code.strip()}
```

## Existing Tests
```python
{tests.strip() if tests.strip() else "# No existing tests provided"}
```

## Already Detected by Static Analysis
Functions: {', '.join(func_names) if func_names else 'none'}
Branches: {', '.join(branch_conditions) if branch_conditions else 'none'}
Already flagged missing: {', '.join(ast_missing) if ast_missing else 'none'}

## Your Task
Return a JSON object with these exact keys:

{{
  "extra_missing_tests": [
    {{
      "scenario": "short description of the missing test scenario",
      "reason": "why this scenario should be tested",
      "risk": "high|medium|low",
      "function_name": "name of the function this applies to"
    }}
  ],
  "extra_edge_cases": [
    {{
      "description": "description of the edge case",
      "type": "boundary|invalid_input|null|overflow|logic|type_error",
      "function_name": "name of the function"
    }}
  ],
  "risk_level": "high|medium|low",
  "summary": "2-3 sentence summary of the test coverage gaps using cautious language"
}}

IMPORTANT RULES:
- Use language like "Potential missing test", "Recommended scenario", "Detected untested branch"
- NEVER claim "100% coverage", "guarantees no bugs", or "provably correct"
- Do NOT repeat the scenarios already detected by static analysis
- Focus on logic edge cases, type errors, None inputs, and domain-specific scenarios
- If no additional scenarios are found, return empty arrays
- Keep the summary factual and developer-focused
- Return ONLY valid JSON. No markdown fences, no explanation outside the JSON.
"""
    return prompt


def analyze_with_ai(code: str, tests: str, ast_results: dict) -> dict:
    """
    Call Gemini to enhance the AST analysis results.

    Returns a dict with:
    - ai_available: bool
    - extra_missing_tests: list
    - extra_edge_cases: list
    - risk_level: str
    - summary: str
    """
    fallback = {
        "ai_available": False,
        "extra_missing_tests": [],
        "extra_edge_cases": [],
        "risk_level": ast_results.get("risk_level", "unknown"),
        "summary": ast_results.get("summary", "AI analysis unavailable. Showing static analysis results only."),
    }

    if not _GEMINI_AVAILABLE or _client is None:
        return fallback

    try:
        prompt = _build_analysis_prompt(code, tests, ast_results)

        response = _client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
                "max_output_tokens": 1500,
            },
        )

        content = response.text.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)

        return {
            "ai_available": True,
            "extra_missing_tests": data.get("extra_missing_tests", []),
            "extra_edge_cases": data.get("extra_edge_cases", []),
            "risk_level": data.get("risk_level", ast_results.get("risk_level", "medium")),
            "summary": data.get("summary", ast_results.get("summary", "")),
        }

    except Exception as e:
        # Any failure — network, quota, JSON parse — falls back gracefully
        fallback["summary"] = (
            ast_results.get("summary", "") +
            f" (AI analysis temporarily unavailable: {type(e).__name__})"
        )
        return fallback
