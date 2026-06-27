"""Utility helpers for the TestFlow Streamlit app."""

from pathlib import Path
import re
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path):
    """Read a project file by relative path, returning None if it is missing."""
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def generated_test_path(target_file):
    """Return the generated test path for a target file."""
    module_name = Path(target_file).stem
    return f"generated_tests/test_{module_name}.py"


def format_percent(value):
    """Format a float percentage for Streamlit metrics."""
    if value is None:
        return "n/a"
    return f"{value * 100:.0f}%"


def parse_percent(stdout, label):
    """Parse a percentage line such as 'Final coverage: 84%' from stdout."""
    pattern = rf"{re.escape(label)}:\s*([0-9]+(?:\.[0-9]+)?)%"
    match = re.search(pattern, stdout)
    if not match:
        return None
    return float(match.group(1)) / 100


def run_testflow_cli(target_file, coverage_target=0.95, max_iterations=12, timeout_seconds=90):
    """Run the TestFlow CLI and return a safe result dictionary."""
    command = [
        "python",
        "main.py",
        "--target",
        target_file,
        "--coverage-threshold",
        str(coverage_target),
        "--max-iterations",
        str(max_iterations),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": " ".join(command),
            "return_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "error": "",
        }
    except FileNotFoundError as exc:
        return {
            "command": " ".join(command),
            "return_code": 127,
            "stdout": "",
            "stderr": str(exc),
            "error": "python command was not found",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": " ".join(command),
            "return_code": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "error": "command timed out",
        }


def build_live_summary(target_file, cli_result, max_iterations):
    """Build a summary dictionary from a live CLI result."""
    stdout = cli_result.get("stdout", "")
    pass_rate = parse_percent(stdout, "Final pass rate")
    coverage = parse_percent(stdout, "Final coverage")
    return {
        "target_file": target_file,
        "actions_taken": ["live_run"],
        "pass_rate": pass_rate if pass_rate is not None else 0.0,
        "coverage": coverage,
        "iterations": max_iterations,
        "repairs_triggered": None,
        "generated_tests_count": None,
        "pytest_stdout": stdout,
        "pytest_stderr": cli_result.get("stderr", ""),
        "return_code": cli_result.get("return_code"),
        "command": cli_result.get("command"),
        "status": "success" if cli_result.get("return_code") == 0 else "failed",
        "note": "Use Demo Mode as the safe public App URL path if runtime integration is unavailable.",
    }
