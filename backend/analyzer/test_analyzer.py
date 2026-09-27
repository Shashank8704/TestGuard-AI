"""
test_analyzer.py — Parse existing pytest test code to understand current coverage.

Extracts:
- Test function names
- Which source functions are called in each test
- Number of tests
- Weak assertion detection
"""

import ast
from typing import Set, List, Dict


def _get_all_names(tree: ast.AST) -> Set[str]:
    """Return all Name node ids in the AST (function calls, variables, etc.)."""
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _get_called_names(tree: ast.AST) -> Set[str]:
    """Return all function names that are called anywhere in the AST."""
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return called


def count_tests(test_code: str) -> int:
    """Count the number of test_ prefixed functions in the test code."""
    if not test_code or not test_code.strip():
        return 0
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return 0

    return sum(
        1 for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def get_covered_function_names(test_code: str) -> Set[str]:
    """
    Return the set of non-test function names called anywhere in the test code.
    These are the source functions being exercised by the existing tests.
    """
    if not test_code or not test_code.strip():
        return set()
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return set()

    all_called = _get_called_names(tree)

    # Return only source function names — never test_ functions or builtins
    _BUILTINS = {
        "assert", "raises", "fixture", "mark", "approx", "warns",
        "pytest", "print", "range", "len", "str", "int", "float",
        "list", "dict", "set", "tuple", "type", "isinstance", "hasattr",
        "getattr", "setattr", "delattr", "open", "super", "property",
        "parametrize", "skip", "xfail", "enumerate", "zip", "map",
        "filter", "sorted", "reversed", "any", "all", "sum", "min", "max", "abs",
    }
    return {
        name for name in all_called
        if not name.startswith("test_")
        and not name.startswith("Test")
        and name not in _BUILTINS
    }


def parse_tests(test_code: str) -> Dict:
    """
    Parse test code and return a structured summary:
    {
        "test_functions": [
            {
                "name": "test_adult",
                "calls": ["calculate_discount"],
                "has_assertion": True,
                "line_number": 1,
            }
        ],
        "covered_functions": {"calculate_discount"},
        "test_count": 1,
    }
    """
    if not test_code or not test_code.strip():
        return {"test_functions": [], "covered_functions": set(), "test_count": 0}

    try:
        tree = ast.parse(test_code)
    except SyntaxError as e:
        return {
            "test_functions": [],
            "covered_functions": set(),
            "test_count": 0,
            "error": str(e),
        }

    test_functions = []
    all_covered = set()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue

        called = _get_called_names(ast.Module(body=node.body, type_ignores=[]))
        has_assertion = any(isinstance(child, ast.Assert) for child in ast.walk(node))

        # Filter to source function names only:
        # - exclude test_ and Test prefixed names (those are test helpers, not source)
        # - exclude pytest builtins and common Python builtins
        _BUILTINS = {
            "pytest", "print", "range", "len", "str", "int", "float",
            "list", "dict", "set", "tuple", "raises", "approx", "warns",
            "fixture", "mark", "parametrize", "skip", "xfail",
            "isinstance", "hasattr", "getattr", "setattr", "type",
            "super", "property", "staticmethod", "classmethod",
            "open", "enumerate", "zip", "map", "filter", "sorted",
            "reversed", "any", "all", "sum", "min", "max", "abs",
        }
        source_calls = {
            c for c in called
            if not c.startswith("test_")
            and not c.startswith("Test")
            and c not in _BUILTINS
        }

        all_covered.update(source_calls)
        test_functions.append({
            "name": node.name,
            "calls": list(source_calls),
            "has_assertion": has_assertion,
            "line_number": node.lineno,
        })

    return {
        "test_functions": test_functions,
        "covered_functions": all_covered,
        "test_count": len(test_functions),
    }


def detect_weak_assertions(test_code: str) -> List[dict]:
    """
    Flag tests that have no assertions or only trivial ones (assert True).
    Returns a list of Issue-compatible dicts.
    """
    if not test_code or not test_code.strip():
        return []
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return []

    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue

        assertions = [child for child in ast.walk(node) if isinstance(child, ast.Assert)]

        if not assertions:
            issues.append({
                "description": f"Test '{node.name}' has no assertions — it will always pass regardless of behavior.",
                "severity": "warning",
                "function_name": node.name,
            })
        else:
            # Check for trivially true assertions: assert True
            trivial = all(
                isinstance(a.test, ast.Constant) and a.test.value is True
                for a in assertions
            )
            if trivial:
                issues.append({
                    "description": f"Test '{node.name}' only contains 'assert True' — it does not verify any behavior.",
                    "severity": "warning",
                    "function_name": node.name,
                })

    return issues


def get_covered_scenarios(test_code: str) -> Set[str]:
    """
    Extract a rough set of 'covered scenario' strings from test function names.
    e.g. test_adult_no_discount → {'adult', 'no_discount', 'adult_no_discount'}
    Used for fuzzy matching against branch conditions.
    """
    if not test_code or not test_code.strip():
        return set()
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return set()

    scenarios = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                # Remove test_ prefix, split by _, build scenario strings
                parts = node.name[5:].split("_")
                scenarios.add(node.name[5:])
                scenarios.update(parts)

    return scenarios
