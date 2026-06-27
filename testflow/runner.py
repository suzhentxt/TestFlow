"""Pytest execution helpers for TestFlow."""

from __future__ import annotations

import re
import subprocess
import sys


def run_pytest(test_file: str, cwd: str | None = None) -> dict:
    """Run pytest for a generated test file and return parsed execution signals."""
    if not test_file:
        raise ValueError("test_file is required")

    command = [sys.executable, "-m", "pytest", test_file, "-q"]
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    passed, failed, errors = _parse_pytest_counts(f"{stdout}\n{stderr}")
    total = passed + failed + errors
    pass_rate = passed / total if total else 0.0

    return {
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": pass_rate,
        "traceback": _traceback_text(stdout, stderr, completed.returncode),
    }


def _parse_pytest_counts(output: str) -> tuple[int, int, int]:
    summary = _find_summary_line(output) or output
    passed = 0
    failed = 0
    errors = 0

    for raw_count, raw_kind in re.findall(r"\b(\d+)\s+(passed|failed|failures|error|errors)\b", summary, re.I):
        count = int(raw_count)
        kind = raw_kind.lower()
        if kind == "passed":
            passed = count
        elif kind in {"failed", "failures"}:
            failed = count
        elif kind in {"error", "errors"}:
            errors = count

    return passed, failed, errors


def _find_summary_line(output: str) -> str:
    for line in reversed(output.splitlines()):
        stripped = line.strip("= ").strip()
        if re.search(r"\b\d+\s+(?:passed|failed|failures|errors?|error)\b", stripped, re.I):
            if "::" not in stripped:
                return stripped
    return ""


def _traceback_text(stdout: str, stderr: str, returncode: int) -> str:
    if returncode == 0:
        return ""
    return "\n".join(part for part in (stdout.strip(), stderr.strip()) if part)
