"""
ast_analyzer.py — Python AST-based static code analysis.

Analyzes Python source code to extract:
- Function definitions and their arguments
- If/elif/else branches with conditions
- Numeric boundary comparisons
- Missing test scenarios based on uncovered branches

Coverage status per function:
  untested  — no test calls this function at all
  partial   — at least one test calls it, but some branches are not represented
  covered   — tests appear to exercise the detected branches
"""

import ast
from typing import List, Set


# ── AST Helpers ───────────────────────────────────────────────────────────────

def _node_to_str(node: ast.AST) -> str:
    """Convert an AST node back to a readable string."""
    try:
        return ast.unparse(node)
    except Exception:
        return "<complex expression>"


def _get_comparisons(node: ast.AST) -> List[dict]:
    """Extract all comparison operations from an AST subtree."""
    comparisons = []
    for child in ast.walk(node):
        if isinstance(child, ast.Compare):
            left = _node_to_str(child.left)
            for op, comparator in zip(child.ops, child.comparators):
                op_str = _op_symbol(op)
                right = _node_to_str(comparator)
                comparisons.append({
                    "left": left,
                    "op": op_str,
                    "right": right,
                    "expr": f"{left} {op_str} {right}",
                })
    return comparisons


def _op_symbol(op: ast.AST) -> str:
    """Map AST comparison operator to symbol string."""
    mapping = {
        ast.Lt: "<", ast.LtE: "<=",
        ast.Gt: ">", ast.GtE: ">=",
        ast.Eq: "==", ast.NotEq: "!=",
        ast.Is: "is", ast.IsNot: "is not",
        ast.In: "in", ast.NotIn: "not in",
    }
    return mapping.get(type(op), "?")


def _get_numeric_boundary_values(comparisons: List[dict]) -> List[dict]:
    """From a list of comparisons, extract ones with numeric literals."""
    boundaries = []
    for c in comparisons:
        try:
            val = float(c["right"])
            boundaries.append({
                "variable": c["left"],
                "op": c["op"],
                "value": val,
                "expr": c["expr"],
            })
        except (ValueError, TypeError):
            pass
    return boundaries


def _has_raise_in_body(body: list) -> bool:
    """Return True if any statement in a body list is a Raise node."""
    for node in body:
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                return True
    return False


# ── Public API ────────────────────────────────────────────────────────────────

def parse_functions(code: str) -> List[dict]:
    """
    Parse Python source code and return a list of FunctionInfo-compatible dicts.
    Handles syntax errors gracefully.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [{"error": f"Syntax error in code: {e}"}]

    functions = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Skip test functions — they belong to test code, not source code.
        # Guards against the user including test functions in the source box.
        if node.name.startswith("test_") or node.name.startswith("Test"):
            continue

        args = [arg.arg for arg in node.args.args]

        # Detect return statements
        has_return = any(
            isinstance(child, ast.Return) and child.value is not None
            for child in ast.walk(node)
        )

        # Collect branches within this function
        branches = []
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                condition = _node_to_str(child.test)
                branches.append(condition)

        functions.append({
            "name": node.name,
            "args": args,
            "has_return": has_return,
            "line_number": node.lineno,
            "branch_count": len(branches),
            "branches": branches,
            "coverage_status": "unknown",  # filled in by analyze_code
        })

    return functions


def parse_branches(code: str) -> List[dict]:
    """
    Extract all if/elif branches from the code with condition text and line numbers.
    Each branch records whether its body raises an exception.

    Walks each function's AST body directly so every If node is correctly
    attributed to its enclosing function, including sequential (non-nested) ifs.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    branches = []
    visited_lines: Set[int] = set()

    def _record_if(node: ast.If, parent_func: str):
        """Record this If node and recurse into elif chains."""
        if node.lineno in visited_lines:
            return
        visited_lines.add(node.lineno)

        condition = _node_to_str(node.test)
        comparisons = _get_comparisons(node.test)
        boundaries = _get_numeric_boundary_values(comparisons)
        raises = _has_raise_in_body(node.body)

        branches.append({
            "condition": condition,
            "line": node.lineno,
            "function": parent_func,
            "comparisons": comparisons,
            "boundaries": boundaries,
            "has_else": len(node.orelse) > 0 and not isinstance(node.orelse[0], ast.If),
            "raises": raises,
        })

        # Walk elif chains (orelse contains another If node)
        for child in node.orelse:
            if isinstance(child, ast.If):
                _record_if(child, parent_func)

    def _walk_body(stmts: list, parent_func: str):
        """Walk a list of statements, recording every If node."""
        for stmt in stmts:
            if isinstance(stmt, ast.If):
                _record_if(stmt, parent_func)
                # Also descend into the if/else bodies for nested ifs
                _walk_body(stmt.body, parent_func)
                _walk_body(stmt.orelse, parent_func)
            elif isinstance(stmt, (ast.For, ast.While, ast.With, ast.Try)):
                # Descend into loop/with/try bodies
                for child_list in [
                    getattr(stmt, "body", []),
                    getattr(stmt, "orelse", []),
                    getattr(stmt, "handlers", []),
                    getattr(stmt, "finalbody", []),
                ]:
                    _walk_body(child_list, parent_func)

    # Process each function's body — skip test functions entirely
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_") or node.name.startswith("Test"):
                continue
            _walk_body(node.body, node.name)

    # Top-level ifs not inside any function
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.If) and stmt.lineno not in visited_lines:
            _record_if(stmt, "")

    return branches


def detect_boundary_conditions(code: str) -> List[dict]:
    """
    Find all numeric comparisons in the code that represent testable boundaries.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    all_boundaries = []
    seen = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            comparisons = _get_comparisons(node)
            for b in _get_numeric_boundary_values(comparisons):
                key = (b["variable"], b["op"], b["value"])
                if key not in seen:
                    seen.add(key)
                    val = b["value"]
                    test_values = []
                    if b["op"] in ("<", "<="):
                        test_values = [val - 1, val, val + 1]
                    elif b["op"] in (">", ">="):
                        test_values = [val - 1, val, val + 1]
                    elif b["op"] == "==":
                        test_values = [val - 1, val, val + 1]
                    b["suggested_test_values"] = test_values
                    all_boundaries.append(b)

    return all_boundaries


def _coverage_status(func_name: str, func_branches: list, covered_function_names: Set[str]) -> str:
    """
    Determine per-function coverage status purely from call-site evidence.

    untested  — no test calls this function
    partial   — at least one test calls it; it has branches (some likely untested)
    covered   — at least one test calls it AND it has no detected branches
    """
    called = func_name in covered_function_names
    if not called:
        return "untested"
    if func_branches:
        return "partial"
    return "covered"


def detect_missing_tests(
    functions: List[dict],
    branches: List[dict],
    covered_function_names: Set[str],
    covered_scenarios: Set[str],
) -> List[dict]:
    """
    Cross-reference detected branches and functions against covered test names
    to produce a list of MissingTest-compatible dicts.

    Priority order:
      1. Exception/error paths (raise branches)
      2. Untested branches
      3. Boundary conditions
      4. Invalid inputs
      5. Normal alternate paths

    Deduplication key: (function_name, scenario_key)
    No "definitely uncovered" claims — cautious language throughout.
    """
    missing = []
    seen_scenarios: Set[str] = set()

    def _add(scenario: str, reason: str, risk: str, func_name: str, priority: int):
        key = (func_name, scenario.lower().strip())
        if key in seen_scenarios:
            return
        seen_scenarios.add(key)
        missing.append({
            "scenario": scenario,
            "reason": reason,
            "risk": risk,
            "function_name": func_name,
            "_priority": priority,
        })

    for func in functions:
        func_name = func["name"]
        if "error" in func:
            continue

        is_called = func_name in covered_function_names
        func_branches = [b for b in branches if b.get("function") == func_name]
        boundary_seen: Set[tuple] = set()

        if not is_called and not func_branches:
            # Completely untested, no branches
            _add(
                scenario=f"No test calls '{func_name}'",
                reason=f"No existing test calls '{func_name}'. Consider adding at least one basic test.",
                risk="high",
                func_name=func_name,
                priority=2,
            )
            continue

        for branch in func_branches:
            condition = branch["condition"]
            raises = branch.get("raises", False)
            boundaries = branch.get("boundaries", [])

            # Priority 1: exception/error paths
            if raises:
                _add(
                    scenario=f"Exception path: {condition} in {func_name}",
                    reason=(
                        f"The branch '{condition}' raises an exception. "
                        f"Recommended: test that the exception is raised correctly."
                    ),
                    risk="high",
                    func_name=func_name,
                    priority=1,
                )

            # Priority 2: untested branches (function not called at all)
            elif not is_called:
                _add(
                    scenario=f"Branch '{condition}' in {func_name} (function not called by any test)",
                    reason=(
                        f"No existing test calls '{func_name}', so the branch '{condition}' "
                        f"is not represented in the supplied tests."
                    ),
                    risk="high",
                    func_name=func_name,
                    priority=2,
                )

            else:
                # Priority 2: branch not represented
                _add(
                    scenario=f"Branch not represented: {condition} in {func_name}",
                    reason=(
                        f"The branch '{condition}' in '{func_name}' does not appear to be "
                        f"represented in the supplied tests. Recommended: add a test case for this path."
                    ),
                    risk="medium",
                    func_name=func_name,
                    priority=2,
                )

            # Priority 3: boundary conditions (deduplicated by variable+op+value)
            for boundary in boundaries:
                b_key = (func_name, boundary["variable"], boundary["op"], boundary["value"])
                if b_key in boundary_seen:
                    continue
                boundary_seen.add(b_key)

                val = int(boundary["value"]) if boundary["value"] == int(boundary["value"]) else boundary["value"]
                _add(
                    scenario=f"Boundary: {boundary['expr']} in {func_name}",
                    reason=(
                        f"Recommended boundary test for '{boundary['expr']}' in '{func_name}'. "
                        f"Test at {boundary['variable']}={val} (the boundary), "
                        f"{boundary['variable']}={val - 1} (just below), and "
                        f"{boundary['variable']}={val + 1} (just above)."
                    ),
                    risk="medium",
                    func_name=func_name,
                    priority=3,
                )

    # Sort by priority then by function name for stable output
    missing.sort(key=lambda m: (m["_priority"], m["function_name"]))

    # Strip internal priority key before returning
    for m in missing:
        m.pop("_priority", None)

    return missing


def detect_edge_cases(functions: List[dict], branches: List[dict]) -> List[dict]:
    """
    Infer edge cases from function signatures AND branch conditions actually
    present in the source code.

    Deduplication key: (function_name, variable, category)

    Only generates edge cases grounded in the actual code:
    - Numeric args that appear in comparisons → zero / negative
    - String args that appear in equality comparisons → empty / None
    - Args compared to None → None input
    - Branches that raise → already covered by missing_tests; skip here
    """
    edge_cases = []
    seen: Set[tuple] = set()

    def _add_ec(desc: str, ec_type: str, func_name: str, dedup_key: tuple):
        if dedup_key in seen:
            return
        seen.add(dedup_key)
        edge_cases.append({
            "description": desc,
            "type": ec_type,
            "function_name": func_name,
        })

    for func in functions:
        func_name = func["name"]
        if "error" in func:
            continue

        args = func.get("args", [])
        func_branches = [b for b in branches if b.get("function") == func_name]

        # Gather all comparisons in this function's branches
        all_comparisons = []
        for b in func_branches:
            all_comparisons.extend(b.get("comparisons", []))

        # Build sets of args involved in numeric vs string comparisons
        numeric_compared_args: Set[str] = set()
        string_compared_args: Set[str] = set()
        none_compared_args: Set[str] = set()

        for cmp in all_comparisons:
            left = cmp["left"]
            right = cmp["right"]
            # Numeric: right side is a number literal
            try:
                float(right)
                if left in args:
                    numeric_compared_args.add(left)
            except (ValueError, TypeError):
                pass
            # String equality: right side is a quoted string
            if right.startswith(("'", '"')) and left in args:
                string_compared_args.add(left)
            # None comparison
            if right in ("None", "null") and left in args:
                none_compared_args.add(left)

        # --- Edge cases grounded in actual comparisons ---

        for arg in numeric_compared_args:
            # Suggest "negative" only when the source code explicitly checks a
            # negative/zero boundary for this arg (e.g. price < 0, weight <= 0).
            # This avoids inventing "negative age" when no such check exists.
            has_explicit_negative_check = any(
                arg in b.get("condition", "") and
                any(
                    bd["variable"] == arg and float(bd["value"]) <= 0
                    for bd in b.get("boundaries", [])
                )
                for b in func_branches
            )
            # Don't duplicate: if there's already a raise-branch for this arg,
            # missing_tests covers it as a high-priority exception path.
            has_raise_for_arg = any(
                b.get("raises") and arg in b.get("condition", "")
                for b in func_branches
            )

            if has_explicit_negative_check and not has_raise_for_arg:
                _add_ec(
                    desc=f"Negative value for '{arg}' in {func_name}",
                    ec_type="invalid_input",
                    func_name=func_name,
                    dedup_key=(func_name, arg, "negative"),
                )

            # Zero is a boundary worth testing for any numerically-compared arg
            _add_ec(
                desc=f"Zero value for '{arg}' in {func_name}",
                ec_type="boundary",
                func_name=func_name,
                dedup_key=(func_name, arg, "zero"),
            )

        for arg in string_compared_args:
            _add_ec(
                desc=f"Empty string for '{arg}' in {func_name}",
                ec_type="boundary",
                func_name=func_name,
                dedup_key=(func_name, arg, "empty_string"),
            )
            _add_ec(
                desc=f"Unrecognised value for '{arg}' in {func_name} (falls through to default path)",
                ec_type="logic",
                func_name=func_name,
                dedup_key=(func_name, arg, "unknown_string"),
            )

        for arg in none_compared_args:
            _add_ec(
                desc=f"None value for '{arg}' in {func_name}",
                ec_type="null",
                func_name=func_name,
                dedup_key=(func_name, arg, "none"),
            )

    return edge_cases


def analyze_code(
    code: str,
    covered_function_names: Set[str] = None,
    covered_scenarios: Set[str] = None,
) -> dict:
    """
    Master analysis function. Returns a dict matching AnalyzeResponse fields
    (minus ai_available and test_count_before — set by the caller).
    """
    if covered_function_names is None:
        covered_function_names = set()
    if covered_scenarios is None:
        covered_scenarios = set()

    functions = parse_functions(code)
    branches = parse_branches(code)

    # Attach coverage_status to each function
    for func in functions:
        if "error" in func:
            continue
        func_branches = [b for b in branches if b.get("function") == func["name"]]
        func["coverage_status"] = _coverage_status(
            func["name"], func_branches, covered_function_names
        )

    missing_tests = detect_missing_tests(functions, branches, covered_function_names, covered_scenarios)
    edge_cases = detect_edge_cases(functions, branches)

    # Compute risk level
    high_count = sum(1 for m in missing_tests if m.get("risk") == "high")
    medium_count = sum(1 for m in missing_tests if m.get("risk") == "medium")

    if high_count >= 2 or (high_count >= 1 and len(functions) <= 2):
        risk_level = "high"
    elif high_count >= 1 or medium_count >= 2:
        risk_level = "medium"
    elif medium_count >= 1 or len(missing_tests) > 0:
        risk_level = "low"
    else:
        risk_level = "low"

    func_names = [f["name"] for f in functions if "error" not in f]
    partial = sum(1 for f in functions if f.get("coverage_status") == "partial")
    untested = sum(1 for f in functions if f.get("coverage_status") == "untested")

    coverage_note = ""
    if untested:
        coverage_note = f"{untested} function(s) not called by any existing test. "
    elif partial:
        coverage_note = f"{partial} function(s) partially tested (some branches not represented). "

    summary = (
        f"{len(func_names)} function(s) analyzed. "
        f"{len(branches)} branch(es) detected. "
        + coverage_note +
        f"{len(missing_tests)} potential missing test scenario(s) identified. "
        f"Risk level: {risk_level.upper()}."
    )

    return {
        "functions": functions,
        "branches": branches,
        "missing_tests": missing_tests,
        "edge_cases": edge_cases,
        "risk_level": risk_level,
        "summary": summary,
    }
