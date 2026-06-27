"""Runtime state for TestFlow orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar


class Action(str, Enum):
    """Planner actions supported by the TestFlow runtime."""

    ANALYZE = "analyze"
    FIND_EDGE_CASES = "find_edge_cases"
    GENERATE_TESTS = "generate_tests"
    RUN_TESTS = "run_tests"
    REPAIR_TESTS = "repair_tests"
    MEASURE_COVERAGE = "measure_coverage"
    GENERATE_MISSING_TESTS = "generate_missing_tests"
    VERIFY_TESTS = "verify_tests"
    STOP = "stop"


@dataclass
class TestFlowState:
    """Mutable runtime snapshot shared across planner-selected actions."""

    __test__: ClassVar[bool] = False

    # Core
    target_file: str = ""
    test_file: str | None = None
    module_name: str = ""
    source_code: str = ""
    generated_tests: str = ""

    # Analysis
    functions: list[Any] = field(default_factory=list)
    classes: list[Any] = field(default_factory=list)
    imports: list[Any] = field(default_factory=list)
    exceptions: list[Any] = field(default_factory=list)
    edge_cases: dict[str, list[str]] = field(default_factory=dict)

    # Execution
    pytest_stdout: str = ""
    pytest_stderr: str = ""
    traceback: str = ""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    pass_rate: float = 0.0

    # Coverage
    coverage: float = 0.0
    coverage_threshold: float | None = None
    coverage_target: float = 0.95

    # Runtime flags
    has_tests: bool = False
    syntax_error: bool = False
    import_error: bool = False
    generation_failed: bool = False
    coverage_measured: bool = False
    verified: bool = False

    # Control
    iterations: int = 0
    max_iterations: int = 12
    actions_taken: list[str] = field(default_factory=list)
    decision_trace: list[dict[str, Any]] = field(default_factory=list)
    status: str = "initialized"
    stop_reason: str = ""

    def __post_init__(self) -> None:
        """Normalize backwards-compatible coverage fields."""
        if self.coverage_threshold is None:
            self.coverage_threshold = self.coverage_target
        else:
            self.coverage_target = self.coverage_threshold
        if self.test_file == "":
            self.test_file = None

    @property
    def iteration(self) -> int:
        """Backward-compatible alias for older code/tests."""
        return self.iterations

    @iteration.setter
    def iteration(self, value: int) -> None:
        self.iterations = value

    def add_action(self, action: Action | str) -> None:
        """Record an executed action in order."""
        self.actions_taken.append(_action_value(action))

    def add_decision(
        self,
        action: Action | str,
        reason: str,
        step: int | None = None,
        status_before: str | None = None,
    ) -> None:
        """Record why the planner selected an action."""
        self.decision_trace.append(
            {
                "step": len(self.decision_trace) if step is None else step,
                "status_before": self.status if status_before is None else status_before,
                "action": _action_value(action),
                "reason": reason,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable state snapshot."""
        return asdict(self)

    def to_summary_dict(self) -> dict[str, Any]:
        """Return the judge-facing summary data."""
        total_tests = self.total_tests or self.passed + self.failed + self.errors
        return {
            "target_file": _display_path(self.target_file),
            "test_file": _display_path(self.test_file),
            "actions_taken": list(self.actions_taken),
            "decision_trace": list(self.decision_trace),
            "pass_rate": self.pass_rate,
            "coverage": self.coverage,
            "total_tests": total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "functions_discovered": len(self.functions),
            "iterations": self.iterations,
            "max_iterations": self.max_iterations,
            "coverage_threshold": self.coverage_threshold,
            "status": self.status,
            "stop_reason": self.stop_reason,
        }

    def report_dict(self) -> dict[str, Any]:
        """Return report data with legacy keys kept for compatibility."""
        summary = self.to_summary_dict()
        summary.update(
            {
                "target": summary["target_file"],
                "generated_test_file": summary["test_file"],
                "actions": summary["actions_taken"],
                "final_pass_rate": self.pass_rate,
                "final_pass_rate_percent": _percent(self.pass_rate),
                "final_coverage": self.coverage,
                "final_coverage_percent": _percent(self.coverage),
                "pytest": {
                    "passed": self.passed,
                    "failed": self.failed,
                    "errors": self.errors,
                    "total": summary["total_tests"],
                },
            }
        )
        return summary

    def summary_text(self) -> str:
        """Return a readable runtime report with planner decisions."""
        total_tests = self.total_tests or self.passed + self.failed + self.errors
        decision_lines: list[str] = []
        for item in self.decision_trace:
            action = item.get("action", "unknown")
            status_before = item.get("status_before", "unknown")
            step = item.get("step", len(decision_lines))
            reason = item.get("reason", "")
            decision_lines.append(f"[{step}] {status_before} -> {action}")
            decision_lines.append(f"    reason: {reason}")
        if not decision_lines:
            decision_lines = ["- none"]

        lines = [
            "========== TestFlow Report ==========",
            "TestFlow Runtime Summary",
            f"Target: {_display_path(self.target_file)}",
            f"Generated test file: {_display_path(self.test_file)}",
            "",
            "Decision trace:",
            *decision_lines,
            "",
            "Final metrics:",
            f"Pass rate: {_percent(self.pass_rate)}%",
            f"Coverage: {_percent(self.coverage)}%",
            f"Pytest: {self.passed} passed, {self.failed} failed, {self.errors} errors, {total_tests} total",
            f"Functions discovered: {len(self.functions)}",
            f"Iterations: {self.iterations}/{self.max_iterations}",
            f"Status: {self.status}",
        ]
        if self.stop_reason:
            lines.append(f"Stop reason: {self.stop_reason}")
        lines.append("====================================")
        return "\n".join(lines)


def _action_value(action: Action | str) -> str:
    if isinstance(action, Action):
        return action.value
    return str(action)


def _percent(value: float | None) -> int:
    try:
        number = float(value if value is not None else 0.0)
    except (TypeError, ValueError):
        number = 0.0
    return int(round(max(0.0, min(1.0, number)) * 100))


def _display_path(value: str | None) -> str:
    if not value:
        return "not set"

    path = Path(value).expanduser()
    try:
        resolved = path.resolve()
        cwd = Path.cwd().resolve()
        return resolved.relative_to(cwd).as_posix()
    except (OSError, ValueError):
        return path.as_posix()
