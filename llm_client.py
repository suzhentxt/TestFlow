"""Small, replaceable LLM client boundary for TestFlow."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_env_file(path: str = ".env") -> None:
    """Load simple KEY=VALUE entries from .env without adding a dependency."""
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()


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
        self.api_key = _env_secret("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = timeout
        self.last_used_fallback = False

    def generate(self, prompt: str) -> str:
        self.last_used_fallback = False
        output = ""
        error = ""
        if not self.api_key:
            self.last_used_fallback = True
            output = self._fallback(prompt)
        else:
            try:
                output = self._call_openai(prompt)
            except Exception as exc:
                error = str(exc)
                self.last_used_fallback = True
                output = self._fallback(prompt)

        _trace_llm_generation(
            prompt=prompt,
            output=output,
            model=self.model,
            used_fallback=self.last_used_fallback,
            error=error,
        )
        return output

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


class _LangfuseTracer:
    def __init__(self) -> None:
        self.client: Any | None = None
        self.enabled = _truthy(os.getenv("LANGFUSE_ENABLED", "true"))
        if not self.enabled:
            return
        public_key = _env_secret("LANGFUSE_PUBLIC_KEY")
        secret_key = _env_secret("LANGFUSE_SECRET_KEY")
        if not public_key or not secret_key:
            return
        try:
            from langfuse import Langfuse
        except Exception:
            return

        try:
            self.client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=_env_host("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
        except Exception:
            self.client = None

    def generation(
        self,
        *,
        prompt: str,
        output: str,
        model: str,
        used_fallback: bool,
        error: str,
    ) -> None:
        if self.client is None:
            return

        metadata = {
            "used_fallback": used_fallback,
            "error": error,
            "prompt_chars": len(prompt),
            "output_chars": len(output),
        }
        trace_input = _trace_payload(prompt, "prompt")
        trace_output = _trace_payload(output, "output")

        try:
            with self.client.start_as_current_observation(
                name="llm-client-generate",
                as_type="generation",
                model=model,
                input=trace_input,
                output=trace_output,
                metadata=metadata,
                level="ERROR" if error else "DEFAULT",
                status_message=error or None,
            ):
                self.client.set_current_trace_io(input=trace_input, output=trace_output)
        except Exception:
            return

    def flush(self) -> None:
        if self.client is None:
            return
        try:
            self.client.flush()
        except Exception:
            return


_TRACER: _LangfuseTracer | None = None


def flush_traces() -> None:
    """Flush pending Langfuse traces for short-lived CLI runs."""
    _get_tracer().flush()


def _trace_llm_generation(
    *,
    prompt: str,
    output: str,
    model: str,
    used_fallback: bool,
    error: str,
) -> None:
    _get_tracer().generation(
        prompt=prompt,
        output=output,
        model=model,
        used_fallback=used_fallback,
        error=error,
    )


def _get_tracer() -> _LangfuseTracer:
    global _TRACER
    if _TRACER is None:
        _TRACER = _LangfuseTracer()
    return _TRACER


def _trace_payload(value: str, label: str) -> str | dict[str, Any]:
    if _truthy(os.getenv("LANGFUSE_CAPTURE_IO", "false")):
        return value
    return {
        "redacted": True,
        "field": label,
        "chars": len(value),
        "message": "Set LANGFUSE_CAPTURE_IO=true to send full prompt/output.",
    }


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_secret(name: str) -> str | None:
    value = (os.getenv(name) or "").strip()
    if not value or value.startswith("replace-with-") or "your-" in value:
        return None
    return value


def _env_host(name: str, default: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value or value.startswith("replace-with-") or "your-" in value:
        return default
    return value
