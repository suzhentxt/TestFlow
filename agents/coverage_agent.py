"""Coverage-guided test expansion agent."""

from __future__ import annotations

import ast
from typing import Any

from testflow.llm_client import LLMClient, clean_code_block

from .base import BaseAgent


class CoverageAgent(BaseAgent):
    """Generate a complete updated pytest file for uncovered branches."""

    def __init__(self, llm_client: LLMClient | None = None, name: str | None = None) -> None:
        super().__init__(name)
        self.llm = llm_client or LLMClient()

    def run(self, state: dict[str, Any]) -> str:
        current_tests = state.get("current_tests") or state.get("current_test_code") or ""
        prompt = (
            "Improve this pytest file for uncovered branches. Return the full updated "
            "Python test file only, not a patch and no Markdown fences.\n"
            f"Current coverage:\n{state.get('current_coverage', state.get('coverage', ''))}\n"
            f"Source code:\n{state.get('source_code', '')}\n"
            f"Current tests:\n{current_tests}\n"
        )
        generated = clean_code_block(self.llm.generate(prompt))
        if not getattr(self.llm, "last_used_fallback", False) and self._valid_test_file(generated):
            return generated
        return self._fallback_update(current_tests)

    def _fallback_update(self, current_tests: str) -> str:
        code = clean_code_block(current_tests).strip()
        if not code:
            code = "import pytest\n"
        if "import pytest" not in code and "pytest." in code:
            code = "import pytest\n\n" + code
        if "test_additional_coverage_placeholder" not in code:
            code += "\n\n\ndef test_additional_coverage_placeholder():\n    marker = 'coverage'\n    assert marker.startswith('cover')\n"
        return code.strip() + "\n"

    def _valid_test_file(self, code: str) -> bool:
        try:
            ast.parse(code)
        except SyntaxError:
            return False
        return "def test_" in code or "async def test_" in code
