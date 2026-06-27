"""Static verification heuristics for generated pytest files."""

from __future__ import annotations

import ast
from collections import Counter
from typing import Any

from .base import BaseAgent


class VerifierAgent(BaseAgent):
    """Check generated tests for common MVP-quality problems."""

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        code = state.get("test_code") or state.get("current_test_code") or state.get("current_tests") or ""
        issues: list[dict[str, Any]] = []
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return {
                "ok": False,
                "issues": [
                    {
                        "type": "syntax_error",
                        "message": exc.msg,
                        "line": exc.lineno,
                    }
                ],
            }

        test_functions = [
            node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        ]
        counts = Counter(function.name for function in test_functions)
        for name, count in counts.items():
            if count > 1:
                issues.append({"type": "duplicate_test", "message": f"{name} appears {count} times."})

        body_counts = Counter(self._body_fingerprint(function) for function in test_functions)
        for function in test_functions:
            if body_counts[self._body_fingerprint(function)] > 1:
                issues.append(
                    {
                        "type": "duplicate_test_body",
                        "message": f"{function.name} has the same body as another test.",
                        "line": function.lineno,
                    }
                )

        for function in test_functions:
            if not self._has_assertion(function):
                issues.append({"type": "missing_assertion", "message": f"{function.name} has no assertion.", "line": function.lineno})
            if self._has_weak_assertion(function):
                issues.append({"type": "weak_assertion", "message": f"{function.name} has an obviously weak assertion.", "line": function.lineno})
            if self._has_flaky_pattern(function):
                issues.append({"type": "flaky_pattern", "message": f"{function.name} uses a flaky pattern.", "line": function.lineno})

        return {"ok": not issues, "issues": issues, "test_count": len(test_functions)}

    def _has_assertion(self, function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return any(isinstance(node, ast.Assert) or self._is_pytest_raises(node) for node in ast.walk(function))

    def _has_weak_assertion(self, function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for node in ast.walk(function):
            if isinstance(node, ast.Assert):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    return True
                if isinstance(node.test, ast.Compare):
                    left = node.test.left
                    comparators = node.test.comparators
                    if (
                        len(comparators) == 1
                        and isinstance(left, ast.Constant)
                        and isinstance(comparators[0], ast.Constant)
                        and left.value == comparators[0].value
                    ):
                        return True
        return False

    def _has_flaky_pattern(self, function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        flaky_names = {"sleep", "time", "random", "randint", "choice", "uuid4", "now", "today"}
        for node in ast.walk(function):
            if isinstance(node, ast.Call):
                name = self._call_name(node.func)
                if any(part in flaky_names for part in name.split(".")):
                    return True
        return False

    def _is_pytest_raises(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.With):
            return False
        for item in node.items:
            context = item.context_expr
            if isinstance(context, ast.Call) and self._call_name(context.func) == "pytest.raises":
                return True
        return False

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = self._call_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ""

    def _body_fingerprint(self, function: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        return "\n".join(ast.dump(statement, include_attributes=False) for statement in function.body)
