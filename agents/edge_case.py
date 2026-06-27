"""Rule-based edge case discovery."""

from __future__ import annotations

import re
from typing import Any

from .base import BaseAgent


class EdgeCaseAgent(BaseAgent):
    """Suggest practical edge cases from function names and signatures."""

    def run(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        analysis = state.get("analysis") or state.get("analyzer_output") or {}
        functions = list(analysis.get("functions", []))
        for class_info in analysis.get("classes", []):
            functions.extend(class_info.get("methods", []))
        return [self._cases_for(function) for function in functions]

    def _cases_for(self, function: dict[str, Any]) -> dict[str, Any]:
        name = function.get("name", "")
        signature = function.get("signature", f"{name}()")
        args = function.get("args", [])
        lowered = name.lower()
        cases: list[str] = []

        if self._contains(lowered, "divide", "div", "ratio", "percent"):
            cases.append("zero denominator")
        if self._contains(lowered, "sort", "sorted", "order"):
            cases.extend(["empty list", "duplicates", "already sorted input"])
        if self._contains(lowered, "parse", "load", "decode"):
            cases.extend(["invalid input", "empty input", "malformed input"])
        if self._contains(lowered, "get_item", "getitem", "get_", "find", "lookup"):
            cases.extend(["missing key/index", "none input"])
        if self._contains(lowered, "read", "open"):
            cases.extend(["missing file", "empty file"])
        if self._contains(lowered, "validate", "check"):
            cases.extend(["invalid value", "boundary value"])
        if self._contains(lowered, "add", "sum", "total"):
            cases.extend(["empty input", "negative numbers"])
        if self._contains(lowered, "remove", "delete", "pop"):
            cases.extend(["missing item", "empty collection"])

        arg_text = " ".join(args).lower()
        signature_text = signature.lower()
        if re.search(r"denominator|divisor|count|limit|size|index", arg_text) and "zero denominator" not in cases:
            cases.append("zero or out-of-range numeric argument")
        if "list" in signature_text or "items" in arg_text or "values" in arg_text:
            if "empty list" not in cases:
                cases.append("empty collection")
            cases.append("single item collection")
        if "str" in signature_text or "text" in arg_text or "name" in arg_text:
            if "empty input" not in cases:
                cases.append("empty string")
            cases.append("whitespace string")
        if ("dict" in signature_text or "key" in arg_text) and "missing key/index" not in cases:
            cases.append("missing key")

        if not cases:
            cases.extend(["typical input", "none input", "boundary input"])

        return {"function": name, "signature": signature, "edge_cases": self._dedupe(cases)}

    def _contains(self, value: str, *needles: str) -> bool:
        return any(needle in value for needle in needles)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                result.append(value)
                seen.add(value)
        return result
