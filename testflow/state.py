"""Runtime state for TestFlow orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


_ACTION_LABELS = {
    "analyze_target": "analyze",
    "generate_initial_tests": "generate_tests",
    "run_pytest_initial": "run_tests",
    "run_pytest_after_repair": "run_tests",
    "run_pytest_after_coverage": "run_tests",
    "repair_tests": "repair_failed_tests",
    "measure_coverage": "measure_coverage",
    "measure_coverage_final": "measure_coverage",
    "improve_coverage": "generate_missing_tests",
    "max_iterations_reached": "max_iterations_reached",
}

_HIDDEN_ACTIONS = {
    "prepare_generated_tests",
    "save_generated_tests",
    "finalize",
}

_STATUS_LABELS = {
    "passed": "completed",
    "completed": "completed",
    "coverage_below_target": "coverage_below_target",
    "failing": "failed",
    "running": "running",
    "initialized": "initialized",
}


@dataclass
class TestFlowState:
    """Mutable runtime snapshot shared across TestFlow runtime steps."""

    target_file: str = ""
    test_file: str = ""
    module_name: str = ""
    functions: list[Any] = field(default_factory=list)
    generated_tests: str = ""
    pytest_stdout: str = ""
    pytest_stderr: str = ""
    traceback: str = ""
    pass_rate: float = 0.0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    coverage: float = 0.0
    actions_taken: list[str] = field(default_factory=list)
    status: str = "initialized"
    iteration: int = 0
    max_iterations: int = 8
    coverage_target: float = 0.8

    def add_action(self, action: str) -> None:
        """Record a runtime action in execution order."""
        self.actions_taken.append(action)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable state snapshot."""
        return asdict(self)

    def report_dict(self) -> dict[str, Any]:
        """Return the judge-facing report data used by summary_text."""
        return {
            "target": _display_path(self.target_file),
            "generated_test_file": _display_path(self.test_file),
            "actions": _display_actions(self.actions_taken),
            "final_pass_rate": self.pass_rate,
            "final_pass_rate_percent": _percent(self.pass_rate),
            "final_coverage": self.coverage,
            "final_coverage_percent": _percent(self.coverage),
            "status": _display_status(self.status),
            "pytest": {
                "passed": self.passed,
                "failed": self.failed,
                "errors": self.errors,
                "total": self.passed + self.failed + self.errors,
            },
            "iterations": {
                "current": self.iteration,
                "max": self.max_iterations,
            },
            "functions_discovered": len(self.functions),
        }

    def summary_text(self) -> str:
        """Return a readable deterministic runtime report."""
        report = self.report_dict()
        total_tests = self.passed + self.failed + self.errors
        action_lines = [f"- {action}" for action in report["actions"]] or ["- none"]

        lines = [
            "========== TestFlow Report ==========",
            "TestFlow Runtime Summary",
            f"Target: {report['target']}",
            f"Generated test file: {report['generated_test_file']}",
            "Actions:",
            *action_lines,
            f"Final pass rate: {report['final_pass_rate_percent']}%",
            f"Final coverage: {report['final_coverage_percent']}%",
            f"Status: {report['status']}",
            f"Pytest: {self.passed} passed, {self.failed} failed, {self.errors} errors, {total_tests} total",
            f"Functions discovered: {len(self.functions)}",
            f"Iterations: {self.iteration}/{self.max_iterations}",
        ]

        raw_trace = _unknown_action_trace(self.actions_taken)
        if raw_trace:
            lines.extend(["Action trace:", *raw_trace])

        lines.append("====================================")
        return "\n".join(lines)


def _display_actions(actions: list[str]) -> list[str]:
    visible_actions = []
    seen = set()

    for action in actions:
        if action in _HIDDEN_ACTIONS:
            continue
        label = _ACTION_LABELS.get(action, action)
        if label not in seen:
            visible_actions.append(label)
            seen.add(label)

    return visible_actions


def _unknown_action_trace(actions: list[str]) -> list[str]:
    unknown_actions = [
        action for action in actions if action not in _ACTION_LABELS and action not in _HIDDEN_ACTIONS
    ]
    return [f"{index}. {action}" for index, action in enumerate(unknown_actions, 1)]


def _display_status(status: str) -> str:
    return _STATUS_LABELS.get(status, status or "unknown")


def _percent(value: float) -> int:
    return int(round(max(0.0, min(1.0, value)) * 100))


def _display_path(value: str) -> str:
    if not value:
        return "not set"

    path = Path(value).expanduser()
    try:
        resolved = path.resolve()
        cwd = Path.cwd().resolve()
        return resolved.relative_to(cwd).as_posix()
    except (OSError, ValueError):
        return path.as_posix()
