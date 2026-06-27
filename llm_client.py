"""Small, replaceable LLM client boundary for TestFlow."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


def clean_code_block(text: str) -> str:
    """Remove Markdown code fences from LLM output."""
    value = (text or "").strip()
    fenced = re.fullmatch(r"```(?:python|py)?\s*\n?(.*?)\n?```", value, re.DOTALL | re.I)
    if fenced:
        return fenced.group(1).strip()
    value = re.sub(r"^\s*```(?:python|py)?\s*$", "", value, flags=re.I | re.M)
    value = re.sub(r"^\s*```\s*$", "", value, flags=re.M)
    return value.strip()


class LLMClient:
    """Tiny wrapper that can be swapped for a richer provider later."""

    def __init__(self, model: str | None = None, timeout: int = 60) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = timeout
        self.last_used_fallback = False

    def generate(self, prompt: str) -> str:
        self.last_used_fallback = False
        if not self.api_key:
            self.last_used_fallback = True
            return self._fallback(prompt)
        try:
            return self._call_openai(prompt)
        except Exception:
            self.last_used_fallback = True
            return self._fallback(prompt)

    def _call_openai(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate concise Python test code or analysis for TestFlow.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API request failed: {details}") from exc
        return data["choices"][0]["message"]["content"]

    def _fallback(self, prompt: str) -> str:
        lower = prompt.lower()
        if "repair" in lower or "fix" in lower:
            return (
                "import pytest\n\n\n"
                "def test_placeholder_repair_keeps_pytest_valid():\n"
                "    marker = 'repair'\n"
                "    assert marker.startswith('rep')\n"
            )
        if "coverage" in lower or "uncovered" in lower:
            return (
                "import pytest\n\n\n"
                "def test_placeholder_additional_coverage():\n"
                "    marker = 'coverage'\n"
                "    assert marker.endswith('age')\n"
            )
        if "pytest" in lower or "test" in lower:
            return (
                "import pytest\n\n\n"
                "def test_placeholder_generated_by_testflow():\n"
                "    marker = 'testflow'\n"
                "    assert marker.startswith('test')\n"
            )
        return "No API key configured; deterministic TestFlow fallback used."
