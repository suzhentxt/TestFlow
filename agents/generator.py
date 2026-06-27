"""Pytest test generation agent."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from testflow.llm_client import LLMClient, clean_code_block

from .base import BaseAgent


class TestGeneratorAgent(BaseAgent):
    """Generate raw pytest code from source analysis and edge cases."""

    def __init__(self, llm_client: LLMClient | None = None, name: str | None = None) -> None:
        super().__init__(name)
        self.llm = llm_client or LLMClient()

    def run(self, state: dict[str, Any]) -> str:
        analysis = state.get("analysis") or state.get("analyzer_output") or {}
        source = state.get("source_code") or analysis.get("source", "")
        edge_cases = state.get("edge_cases", [])
        target_file = state.get("target_file") or analysis.get("path", "target.py")
        prompt = self._prompt(source, analysis, edge_cases, target_file)

        generated = clean_code_block(self.llm.generate(prompt))
        if not getattr(self.llm, "last_used_fallback", False) and self._looks_like_python_tests(generated):
            return generated
        return self._fallback_tests(analysis, edge_cases, target_file)

    def _prompt(self, source: str, analysis: dict[str, Any], edge_cases: list[dict[str, Any]], target_file: str) -> str:
        return (
            "Generate raw Python pytest tests only. Do not include Markdown fences.\n"
            f"Target file: {target_file}\n"
            f"Analysis: {analysis}\n"
            f"Edge cases: {edge_cases}\n"
            f"Source:\n{source}\n"
        )

    def _looks_like_python_tests(self, code: str) -> bool:
        try:
            ast.parse(code)
        except SyntaxError:
            return False
        return "def test_" in code or "async def test_" in code

    def _fallback_tests(self, analysis: dict[str, Any], edge_cases: list[dict[str, Any]], target_file: str) -> str:
        public_functions = [function for function in analysis.get("functions", []) if not function.get("name", "").startswith("_")]
        public_classes = [class_info for class_info in analysis.get("classes", []) if not class_info.get("name", "").startswith("_")]
        edge_map = {item.get("function"): item.get("edge_cases", []) for item in edge_cases}

        lines = self._import_target_lines(target_file)
        initial_line_count = len(lines)
        for function in public_functions:
            lines.extend(self._function_tests(function, edge_map.get(function.get("name"), [])))
        for class_info in public_classes:
            lines.extend(self._class_tests(class_info, edge_map))
        if len(lines) == initial_line_count:
            lines.extend(["", "def test_module_imports():", "    assert target is not None"])
        return "\n".join(lines).rstrip() + "\n"

    def _import_target_lines(self, target_file: str) -> list[str]:
        path = Path(target_file)
        if path.suffix != ".py":
            return ["import pytest", f"import {str(target_file).replace('/', '.').replace(chr(92), '.')} as target", ""]
        return [
            "import importlib.util",
            "import sys",
            "from pathlib import Path",
            "",
            "import pytest",
            "",
            f"_TARGET_PATH = Path(r\"{str(path)}\")",
            "_SPEC = importlib.util.spec_from_file_location('testflow_target', _TARGET_PATH)",
            "assert _SPEC is not None and _SPEC.loader is not None",
            "target = importlib.util.module_from_spec(_SPEC)",
            "sys.modules[_SPEC.name] = target",
            "_SPEC.loader.exec_module(target)",
            "",
        ]

    def _function_tests(self, function: dict[str, Any], cases: list[str]) -> list[str]:
        name = function.get("name", "")
        args = [arg for arg in function.get("args", []) if arg not in ("self", "cls")]
        normal_values = [self._normal_value(arg, name) for arg in args]
        call = f"target.{name}({', '.join(normal_values)})"
        test_name = self._safe_test_name(f"test_{name}_normal_case")
        lines = [
            "",
            f"def {test_name}():",
            f"    result = {call}",
            "    assert result is not None",
        ]

        for case in cases:
            lines.extend(self._edge_test(name, args, case, f"target.{name}"))
        return lines

    def _class_tests(self, class_info: dict[str, Any], edge_map: dict[str, list[str]]) -> list[str]:
        class_name = class_info.get("name", "")
        methods = [
            method
            for method in class_info.get("methods", [])
            if not method.get("name", "").startswith("_") and method.get("name") != "__init__"
        ]
        init_method = next((method for method in class_info.get("methods", []) if method.get("name") == "__init__"), None)
        init_args = [arg for arg in (init_method or {}).get("args", []) if arg not in ("self", "cls")]
        init_values = [self._normal_value(arg, "__init__") for arg in init_args]
        lines: list[str] = []
        for method in methods:
            method_name = method.get("name", "")
            args = [arg for arg in method.get("args", []) if arg not in ("self", "cls")]
            normal_values = [self._normal_value(arg, method_name) for arg in args]
            test_name = self._safe_test_name(f"test_{class_name}_{method_name}_normal_case")
            lines.extend(
                [
                    "",
                    f"def {test_name}():",
                    f"    instance = target.{class_name}({', '.join(init_values)})",
                    f"    result = instance.{method_name}({', '.join(normal_values)})",
                    "    assert result is not None",
                ]
            )
            for case in edge_map.get(method_name, []):
                lines.extend(
                    self._edge_test(
                        method_name,
                        args,
                        case,
                        f"instance.{method_name}",
                        setup=[f"    instance = target.{class_name}({', '.join(init_values)})"],
                        prefix=class_name,
                    )
                )
        return lines

    def _edge_test(
        self,
        function_name: str,
        args: list[str],
        case: str,
        callable_name: str,
        setup: list[str] | None = None,
        prefix: str | None = None,
    ) -> list[str]:
        safe_case = re.sub(r"\W+", "_", case.lower()).strip("_")
        name_parts = ["test"]
        if prefix:
            name_parts.append(prefix)
        name_parts.extend([function_name, safe_case])
        test_name = self._safe_test_name("_".join(name_parts))
        values = [self._normal_value(arg, function_name) for arg in args]
        lowered = case.lower()
        function_lowered = function_name.lower()
        if "zero" in lowered and values:
            values[-1] = "0"
        elif "empty input" in lowered or "empty string" in lowered:
            values = ["''" if index == 0 else value for index, value in enumerate(values)]
        elif "whitespace string" in lowered:
            values = ["'   '" if index == 0 else value for index, value in enumerate(values)]
        elif "empty list" in lowered or "empty collection" in lowered:
            values = ["[]" if index == 0 else value for index, value in enumerate(values)]
        elif "duplicates" in lowered:
            values = ["[2, 1, 2]" if index == 0 else value for index, value in enumerate(values)]
        elif "malformed" in lowered:
            values = ["'12x'" if index == 0 else value for index, value in enumerate(values)]
        elif "invalid" in lowered:
            values = ["'not-valid'" if index == 0 else value for index, value in enumerate(values)]
        elif "missing key" in lowered or "missing key/index" in lowered:
            values = ["{}" if index == 0 else "'missing'" if index == 1 else value for index, value in enumerate(values)]
        elif "none" in lowered:
            values = ["None" if index == 0 else value for index, value in enumerate(values)]
        call = f"{callable_name}({', '.join(values)})"
        setup_lines = setup or []

        if "sort" in function_lowered or "order" in function_lowered:
            expected = "[]"
            if "duplicates" in lowered:
                expected = "[1, 2, 2]"
            elif "already sorted" in lowered:
                values = ["[1, 2, 3]" if index == 0 else value for index, value in enumerate(values)]
                call = f"{callable_name}({', '.join(values)})"
                expected = "[1, 2, 3]"
            elif "single item" in lowered:
                values = ["[1]" if index == 0 else value for index, value in enumerate(values)]
                call = f"{callable_name}({', '.join(values)})"
                expected = "[1]"
            return [
                "",
                f"def {test_name}():",
                *setup_lines,
                f"    result = {call}",
                f"    assert result == {expected}",
            ]

        return [
            "",
            f"def {test_name}():",
            *setup_lines,
            "    with pytest.raises((ValueError, TypeError, KeyError, IndexError, ZeroDivisionError)):",
            f"        {call}",
        ]

    def _normal_value(self, arg: str, function_name: str = "") -> str:
        lowered = arg.lower()
        function_lowered = function_name.lower()
        if "parse" in function_lowered and any(token in lowered for token in ("text", "value", "number", "input")):
            return "'1'"
        if any(token in lowered for token in ("items", "values", "numbers", "nums", "list")):
            return "[1, 2, 3]"
        if "dict" in lowered or "mapping" in lowered or "data" in lowered:
            return "{'a': 1}"
        if "key" in lowered or "name" in lowered or "text" in lowered or "path" in lowered:
            return "'a'"
        if any(token in lowered for token in ("denominator", "divisor")):
            return "2"
        return "1"

    def _safe_test_name(self, value: str) -> str:
        safe = re.sub(r"\W+", "_", value.lower()).strip("_")
        if not safe.startswith("test_"):
            safe = "test_" + safe
        return safe
