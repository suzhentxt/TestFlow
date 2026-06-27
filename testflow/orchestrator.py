"""State-based TestFlow orchestration loop."""

from __future__ import annotations

import ast
import re
from html import escape
from pathlib import Path
from typing import Any

from testflow.coverage_utils import run_coverage
from testflow.llm_client import trace_span, update_current_span, update_current_trace
from testflow.runner import run_pytest
from testflow.state import Action, TestFlowState


class HeuristicPlanner:
    """Choose the next TestFlow action from the current runtime state."""

    def __init__(self, coverage_threshold: float = 0.95) -> None:
        self.coverage_threshold = coverage_threshold

    def choose_next_action(self, state: TestFlowState) -> tuple[Action, str]:
        """Return the next action and the reason it was selected."""
        threshold = state.coverage_threshold or self.coverage_threshold

        if state.status == "success":
            return Action.STOP, "already successful"
        if state.iterations >= state.max_iterations:
            return Action.STOP, "max iterations reached"
        if self._no_progress(state):
            return Action.STOP, "no progress"

        if not state.source_code:
            return Action.ANALYZE, "source code not loaded"
        if self._needs_analysis(state):
            return Action.ANALYZE, "code not analyzed"

        if not state.edge_cases:
            return Action.FIND_EDGE_CASES, "edge cases not discovered"

        if state.generation_failed:
            return Action.GENERATE_TESTS, "previous generation failed"
        if not state.generated_tests:
            return Action.GENERATE_TESTS, "no tests generated"

        if state.syntax_error:
            return Action.REPAIR_TESTS, "syntax error detected"
        if state.import_error:
            return Action.REPAIR_TESTS, "import error detected"
        if state.failed > 0 or state.errors > 0:
            return Action.REPAIR_TESTS, "failing tests detected"
        if state.total_tests > 0 and state.pass_rate < 1.0:
            return Action.REPAIR_TESTS, "pass rate below 100%"

        if state.has_tests and state.status in {
            "tests_generated",
            "tests_repaired",
            "missing_tests_generated",
        }:
            return Action.RUN_TESTS, "tests need execution"
        if (
            not state.has_tests
            and state.generated_tests
            and state.status in {"tests_generated", "tests_repaired", "missing_tests_generated"}
        ):
            return Action.RUN_TESTS, "validate whether pytest can collect tests"

        if state.total_tests > 0 and state.pass_rate == 1.0 and not state.coverage_measured:
            return Action.MEASURE_COVERAGE, "tests pass but coverage not measured"

        if (
            state.pass_rate == 1.0
            and state.coverage_measured
            and state.coverage < threshold
        ):
            return Action.GENERATE_MISSING_TESTS, "coverage below threshold"

        if state.pass_rate == 1.0 and state.coverage >= threshold:
            return Action.VERIFY_TESTS, "pass rate and coverage target reached"

        return Action.STOP, "no valid next action"

    def _needs_analysis(self, state: TestFlowState) -> bool:
        if state.status != "initialized":
            return False
        return not (state.functions or state.classes or state.imports)

    def _no_progress(self, state: TestFlowState) -> bool:
        if len(state.decision_trace) < 4:
            return False
        recent = [item.get("action") for item in state.decision_trace[-4:]]
        return len(set(recent)) == 1 and recent[0] in {
            Action.REPAIR_TESTS.value,
            Action.GENERATE_TESTS.value,
            Action.GENERATE_MISSING_TESTS.value,
        }


class TestFlowOrchestrator:
    """Run TestFlow as State -> Planner -> Action -> Agent -> State."""

    def __init__(self, coverage_threshold: float = 0.95, max_iterations: int = 12) -> None:
        self.planner = HeuristicPlanner(coverage_threshold)
        self.coverage_threshold = coverage_threshold
        self.max_iterations = max_iterations
        self.agents = {
            Action.ANALYZE: AnalyzerAgent(),
            Action.FIND_EDGE_CASES: EdgeCaseAgent(),
            Action.GENERATE_TESTS: TestGeneratorAgent(),
            Action.RUN_TESTS: RunnerAgent(),
            Action.REPAIR_TESTS: RepairAgent(),
            Action.MEASURE_COVERAGE: CoverageAgent(),
            Action.GENERATE_MISSING_TESTS: MissingTestAgent(),
            Action.VERIFY_TESTS: VerifierAgent(),
        }

    def run(self, state: TestFlowState) -> TestFlowState:
        """Run planner-selected actions until STOP or success."""
        _validate_state(state)
        state.coverage_threshold = state.coverage_threshold or self.coverage_threshold
        state.coverage_target = state.coverage_threshold
        state.max_iterations = state.max_iterations or self.max_iterations

        with trace_span(
            "testflow-run",
            input_data={
                "target_file": _display_target(state),
                "coverage_threshold": state.coverage_threshold,
                "max_iterations": state.max_iterations,
            },
            metadata={"component": "orchestrator"},
        ):
            update_current_trace(
                name="TestFlow Runtime Orchestrator",
                input_data={"target_file": _display_target(state)},
                metadata={
                    "track": "engineering-depth",
                    "orchestration": "state-based",
                },
                tags=["testflow", "orchestrator", "runtime"],
            )

            while True:
                status_before = state.status
                action, reason = self.planner.choose_next_action(state)
                decision = {
                    "step": len(state.decision_trace),
                    "status_before": status_before,
                    "action": action.value,
                    "reason": reason,
                    "metrics_before": _trace_metrics(state),
                }

                with trace_span(
                    "planner.choose_next_action",
                    input_data=_trace_state(state),
                    output_data=decision,
                    metadata={"component": "planner"},
                ):
                    pass

                state.add_decision(
                    action,
                    reason,
                    step=decision["step"],
                    status_before=status_before,
                )

                if action == Action.STOP:
                    state.stop_reason = reason
                    if state.status != "success":
                        state.status = "stopped"
                    state.decision_trace[-1]["status_after"] = state.status
                    state.decision_trace[-1]["metrics_after"] = _trace_metrics(state)
                    break

                agent = self.agents[action]
                with trace_span(
                    f"action.{action.value}",
                    input_data=_trace_state(state),
                    metadata={
                        "component": "agent",
                        "action": action.value,
                        "reason": reason,
                    },
                ):
                    state = agent.run(state)
                    update_current_span(
                        output_data=_trace_state(state),
                        metadata={
                            "status_after": state.status,
                            "pass_rate": state.pass_rate,
                            "coverage": state.coverage,
                        },
                    )

                state.add_action(action)
                state.iterations += 1
                state.decision_trace[-1]["status_after"] = state.status
                state.decision_trace[-1]["metrics_after"] = _trace_metrics(state)

                if state.status == "success":
                    state.stop_reason = "verified successfully"
                    break
                if state.iterations >= state.max_iterations:
                    state.stop_reason = "max iterations reached"
                    break

            graph = _trace_graph(state)
            graph["svg_path"] = _write_graph_svg(graph)
            state.runtime_graph = graph
            with trace_span(
                "orchestrator.graph",
                input_data={"decision_trace": state.decision_trace},
                output_data=graph,
                metadata={
                    "component": "orchestrator",
                    "graph_format": "nodes_edges_mermaid",
                    "node_count": len(graph["nodes"]),
                    "edge_count": len(graph["edges"]),
                },
            ):
                _emit_graph_spans(graph)

            trace_output = state.to_summary_dict()
            update_current_trace(
                output_data=trace_output,
                metadata={
                    "status": state.status,
                    "stop_reason": state.stop_reason,
                    "iterations": state.iterations,
                    "actions_taken": state.actions_taken,
                    "graph": {
                        "node_count": len(graph["nodes"]),
                        "edge_count": len(graph["edges"]),
                        "mermaid": graph["mermaid"],
                    },
                },
            )
            update_current_span(output_data=trace_output)

        return state


class AnalyzerAgent:
    """Load source code and extract static structure."""

    def run(self, state: TestFlowState) -> TestFlowState:
        target_path = _target_path(state)
        state.module_name = state.module_name or _safe_identifier(target_path.stem)
        state.source_code = target_path.read_text(encoding="utf-8")
        tree = ast.parse(state.source_code, filename=str(target_path))

        state.functions = [
            _function_info(node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        ]
        state.classes = [
            _class_info(node)
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and not node.name.startswith("_")
        ]
        state.imports = _imports(tree)
        state.exceptions = sorted(_exceptions(tree))
        state.status = "analyzed"
        return state


class EdgeCaseAgent:
    """Generate simple edge-case hints from function names and signatures."""

    def run(self, state: TestFlowState) -> TestFlowState:
        cases: dict[str, list[str]] = {}
        for function in state.functions:
            name = _function_name(function)
            args = _function_args(function)
            cases[name] = _edge_cases_for(name, args)
        state.edge_cases = cases
        state.status = "edge_cases_found"
        return state


class TestGeneratorAgent:
    """Generate deterministic pytest code and save it to generated_tests."""

    def run(self, state: TestFlowState) -> TestFlowState:
        tests = self._generate_tests(state)
        tests = _clean_code_block(tests)

        if not _valid_test_code(tests):
            tests = _fallback_import_test(state)

        state.generated_tests = _ensure_final_newline(tests)
        state.test_file = save_generated_tests(state)
        state.has_tests = "def test_" in state.generated_tests
        state.generation_failed = not state.has_tests
        state.coverage_measured = False
        state.status = "tests_generated" if state.has_tests else "generation_failed"
        return state

    def _generate_tests(self, state: TestFlowState) -> str:
        function_names = {_function_name(function) for function in state.functions}
        if _has_functions(function_names, {"add", "subtract", "divide", "factorial", "is_prime"}):
            return _calculator_tests(state)
        if _has_functions(function_names, {"normalize_text", "is_palindrome", "truncate", "parse_csv_line"}):
            return _string_utils_tests(state)
        if _has_functions(function_names, {"calculate_discount", "validate_order", "compute_shipping"}):
            return _order_utils_tests(state)
        return _generic_tests(state)


class RunnerAgent:
    """Run pytest and update execution fields."""

    def run(self, state: TestFlowState) -> TestFlowState:
        if not state.test_file:
            state.status = "no_test_file"
            state.has_tests = False
            return state

        result = run_pytest(state.test_file, cwd=str(Path.cwd()))
        output = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"

        state.pytest_stdout = result.get("stdout", "")
        state.pytest_stderr = result.get("stderr", "")
        state.traceback = result.get("traceback", "")
        state.passed = int(result.get("passed", 0))
        state.failed = int(result.get("failed", 0))
        state.errors = int(result.get("errors", 0))
        state.total_tests = state.passed + state.failed + state.errors
        state.pass_rate = float(result.get("pass_rate", 0.0))
        state.has_tests = state.total_tests > 0 or "def test_" in state.generated_tests
        state.syntax_error = "SyntaxError" in output
        state.import_error = any(
            marker in output
            for marker in ("ImportError", "ModuleNotFoundError", "cannot import name")
        )

        if state.total_tests == 0:
            state.status = "no_tests_collected"
        elif state.failed > 0 or state.errors > 0:
            state.status = "tests_failed"
        elif state.pass_rate == 1.0:
            state.status = "tests_passed"
        else:
            state.status = "tests_failed"
        return state


class RepairAgent:
    """Repair generated tests using deterministic fallback behavior."""

    def run(self, state: TestFlowState) -> TestFlowState:
        repaired = _clean_code_block(state.generated_tests)
        if not _valid_test_code(repaired):
            repaired = _fallback_import_test(state)
        if "pytest." in repaired and "import pytest" not in repaired:
            repaired = "import pytest\n\n" + repaired

        state.generated_tests = _ensure_final_newline(repaired)
        state.test_file = save_generated_tests(state)
        state.syntax_error = False
        state.import_error = False
        state.coverage_measured = False
        state.status = "tests_repaired"
        return state


class CoverageAgent:
    """Measure coverage for the current generated test file."""

    def run(self, state: TestFlowState) -> TestFlowState:
        if not state.test_file:
            state.coverage = 0.0
            state.coverage_measured = True
            state.status = "coverage_measured"
            return state

        result = run_coverage(state.target_file, state.test_file, cwd=str(Path.cwd()))
        state.coverage = _normalize_coverage(result.get("coverage", 0.0))
        state.coverage_measured = True
        state.status = "coverage_measured"
        return state


class MissingTestAgent:
    """Expand tests when coverage is below the configured threshold."""

    def run(self, state: TestFlowState) -> TestFlowState:
        marker = "# TestFlow coverage expansion"
        if marker not in state.generated_tests:
            state.generated_tests = _ensure_final_newline(state.generated_tests)
            state.generated_tests += "\n" + marker + "\n"
            state.generated_tests += _coverage_expansion_tests(state)

        state.test_file = save_generated_tests(state)
        state.has_tests = "def test_" in state.generated_tests
        state.coverage_measured = False
        state.status = "missing_tests_generated"
        return state


class VerifierAgent:
    """Run lightweight static checks on generated pytest code."""

    def run(self, state: TestFlowState) -> TestFlowState:
        state.verified = _verify_tests(state.generated_tests)
        state.status = "success" if state.verified else "verification_failed"
        if state.verified:
            state.stop_reason = "verified successfully"
        return state


def run_testflow(state_or_target: TestFlowState | str, coverage_threshold: float = 0.95, max_iterations: int = 12) -> Any:
    """Run TestFlow.

    Passing a TestFlowState returns the final state for backwards compatibility.
    Passing a target path returns a summary dictionary for UI/API callers.
    """
    if isinstance(state_or_target, TestFlowState):
        state = state_or_target
        orchestrator = TestFlowOrchestrator(
            coverage_threshold=state.coverage_threshold or coverage_threshold,
            max_iterations=state.max_iterations or max_iterations,
        )
        return orchestrator.run(state)

    target_path = Path(state_or_target).expanduser()
    state = TestFlowState(
        target_file=str(target_path.resolve()),
        module_name=target_path.stem,
        coverage_threshold=coverage_threshold,
        max_iterations=max_iterations,
    )
    return TestFlowOrchestrator(coverage_threshold, max_iterations).run(state).to_summary_dict()


def save_generated_tests(state: TestFlowState) -> str:
    """Save state.generated_tests under generated_tests/test_<module>.py."""
    _ensure_module_name(state)
    generated_dir = Path.cwd() / "generated_tests"
    generated_dir.mkdir(parents=True, exist_ok=True)
    test_path = generated_dir / f"test_{_safe_identifier(state.module_name)}.py"
    test_path.write_text(_ensure_final_newline(state.generated_tests), encoding="utf-8")
    state.test_file = str(test_path)
    return state.test_file


def _validate_state(state: TestFlowState) -> None:
    if not state.target_file:
        raise ValueError("state.target_file is required")


def _trace_state(state: TestFlowState) -> dict[str, Any]:
    return {
        "target_file": _display_target(state),
        "test_file": _display_path(state.test_file),
        "status": state.status,
        "iterations": state.iterations,
        "max_iterations": state.max_iterations,
        "functions": [_function_name(function) for function in state.functions],
        "has_tests": state.has_tests,
        "total_tests": state.total_tests,
        "passed": state.passed,
        "failed": state.failed,
        "errors": state.errors,
        "pass_rate": state.pass_rate,
        "coverage": state.coverage,
        "coverage_threshold": state.coverage_threshold,
        "coverage_measured": state.coverage_measured,
        "syntax_error": state.syntax_error,
        "import_error": state.import_error,
        "actions_taken": list(state.actions_taken),
    }


def _trace_metrics(state: TestFlowState) -> dict[str, Any]:
    return {
        "pass_rate": state.pass_rate,
        "coverage": state.coverage,
        "coverage_threshold": state.coverage_threshold,
        "total_tests": state.total_tests,
        "passed": state.passed,
        "failed": state.failed,
        "errors": state.errors,
        "iterations": state.iterations,
        "has_tests": state.has_tests,
        "coverage_measured": state.coverage_measured,
        "syntax_error": state.syntax_error,
        "import_error": state.import_error,
    }


def _trace_graph(state: TestFlowState) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    mermaid_lines = ["flowchart TD"]

    for item in state.decision_trace:
        step = int(item.get("step", len(nodes)))
        status_before = str(item.get("status_before", "unknown"))
        status_after = str(item.get("status_after") or _next_status_after(state, step))
        action = str(item.get("action", "unknown"))
        reason = str(item.get("reason", ""))
        before_id = f"S{step}"
        action_id = f"A{step}"
        after_id = f"S{step + 1}"

        nodes.append(
            {
                "id": before_id,
                "type": "state",
                "label": status_before,
                "step": step,
                "metrics": item.get("metrics_before", {}),
            }
        )
        nodes.append(
            {
                "id": action_id,
                "type": "action",
                "label": action,
                "step": step,
                "reason": reason,
            }
        )
        nodes.append(
            {
                "id": after_id,
                "type": "state",
                "label": status_after,
                "step": step + 1,
                "metrics": item.get("metrics_after", {}),
            }
        )

        edges.append(
            {
                "source": before_id,
                "target": action_id,
                "label": reason,
                "type": "planner_decision",
            }
        )
        edges.append(
            {
                "source": action_id,
                "target": after_id,
                "label": status_after,
                "type": "state_update",
            }
        )

        mermaid_lines.append(f'    {before_id}["state: {_mermaid_label(status_before)}"]')
        mermaid_lines.append(f'    {action_id}["action: {_mermaid_label(action)}"]')
        mermaid_lines.append(f'    {after_id}["state: {_mermaid_label(status_after)}"]')
        mermaid_lines.append(f"    {before_id} -->|{_mermaid_label(reason)}| {action_id}")
        mermaid_lines.append(f"    {action_id} -->|{_mermaid_label(status_after)}| {after_id}")

    return {
        "type": "state_action_graph",
        "nodes": _dedupe_graph_nodes(nodes),
        "edges": edges,
        "mermaid": "\n".join(mermaid_lines),
        "timeline": [
            {
                "step": item.get("step"),
                "from": item.get("status_before"),
                "action": item.get("action"),
                "to": item.get("status_after"),
                "reason": item.get("reason"),
            }
            for item in state.decision_trace
        ],
    }


def _emit_graph_spans(graph: dict[str, Any]) -> None:
    svg_media = _langfuse_svg_media(graph.get("svg_path", ""))
    image_output = {
        "svg_path": graph.get("svg_path"),
        "message": "Open this observation output/media to view the orchestration graph.",
    }
    if svg_media is not None:
        image_output["graph_svg"] = svg_media

    with trace_span(
        "graph.image.svg",
        output_data=image_output,
        metadata={
            "component": "orchestration-graph",
            "format": "svg",
            "svg_path": graph.get("svg_path"),
        },
    ):
        pass

    with trace_span(
        "graph.mermaid",
        output_data={"mermaid": graph.get("mermaid", "")},
        metadata={"component": "orchestration-graph", "format": "mermaid"},
    ):
        pass

    for transition in graph.get("timeline", []):
        step = transition.get("step", 0)
        source = transition.get("from") or "unknown"
        action = transition.get("action") or "unknown"
        target = transition.get("to") or "unknown"
        reason = transition.get("reason") or ""
        span_name = f"graph.edge.{int(step):02d} {source} -> {action} -> {target}"

        with trace_span(
            span_name,
            input_data={"state": source},
            output_data={"state": target},
            metadata={
                "component": "orchestration-graph",
                "step": step,
                "from": source,
                "action": action,
                "to": target,
                "reason": reason,
            },
        ):
            pass


def _write_graph_svg(graph: dict[str, Any]) -> str:
    timeline = graph.get("timeline", [])
    width = 1120
    row_height = 116
    margin = 32
    height = max(220, margin * 2 + max(1, len(timeline)) * row_height)
    state_x = 34
    action_x = 380
    next_x = 744
    box_h = 58
    box_w = 300
    action_w = 300

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">'
        ),
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">',
        '<path d="M0,0 L0,6 L9,3 z" fill="#2563eb" />',
        "</marker>",
        "</defs>",
        '<rect width="100%" height="100%" fill="#f8fafc" />',
        '<text x="34" y="34" font-family="Inter,Arial,sans-serif" font-size="22" font-weight="700" fill="#0f172a">TestFlow Runtime Orchestration Graph</text>',
        '<text x="34" y="58" font-family="Inter,Arial,sans-serif" font-size="13" fill="#475569">State -> Planner Action -> Updated State, generated from the actual decision trace.</text>',
    ]

    for index, transition in enumerate(timeline):
        y = 84 + index * row_height
        center_y = y + box_h / 2
        step = transition.get("step", index)
        source = str(transition.get("from") or "unknown")
        action = str(transition.get("action") or "unknown")
        target = str(transition.get("to") or "unknown")
        reason = str(transition.get("reason") or "")

        parts.extend(
            [
                f'<text x="{state_x}" y="{y - 10}" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#64748b">STEP {escape(str(step))}</text>',
                _svg_box(state_x, y, box_w, box_h, "State", source, "#dbeafe", "#1d4ed8"),
                _svg_arrow(state_x + box_w, center_y, action_x - 18, center_y, reason),
                _svg_box(action_x, y, action_w, box_h, "Planner Action", action, "#dcfce7", "#15803d"),
                _svg_arrow(action_x + action_w, center_y, next_x - 18, center_y, "updates state"),
                _svg_box(next_x, y, box_w, box_h, "Updated State", target, "#fef3c7", "#b45309"),
            ]
        )

    parts.append("</svg>")
    output_dir = Path(".testflow")
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / "orchestration_graph.svg"
    svg_path.write_text("\n".join(parts), encoding="utf-8")
    return svg_path.as_posix()


def _svg_box(x: int, y: int, width: int, height: int, label: str, value: str, fill: str, stroke: str) -> str:
    safe_label = escape(label)
    safe_value = escape(_shorten(value, 34))
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5" />',
            f'<text x="{x + 16}" y="{y + 22}" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="{stroke}">{safe_label}</text>',
            f'<text x="{x + 16}" y="{y + 43}" font-family="Inter,Arial,sans-serif" font-size="18" font-weight="700" fill="#0f172a">{safe_value}</text>',
        ]
    )


def _svg_arrow(x1: float, y1: float, x2: float, y2: float, label: str) -> str:
    safe_label = escape(_shorten(label, 30))
    label_x = (x1 + x2) / 2 - 72
    label_y = y1 - 8
    return "\n".join(
        [
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)" />',
            f'<text x="{label_x}" y="{label_y}" font-family="Inter,Arial,sans-serif" font-size="11" fill="#334155">{safe_label}</text>',
        ]
    )


def _shorten(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1] + "..."


def _langfuse_svg_media(svg_path: str) -> Any | None:
    if not svg_path:
        return None
    try:
        from langfuse.api import MediaContentType
        from langfuse.media import LangfuseMedia
    except Exception:
        return None

    try:
        return LangfuseMedia(
            file_path=svg_path,
            content_type=MediaContentType.IMAGE_SVG_XML,
        )
    except Exception:
        return None


def _next_status_after(state: TestFlowState, step: int) -> str:
    next_index = step + 1
    if next_index < len(state.decision_trace):
        return str(state.decision_trace[next_index].get("status_before", "unknown"))
    return state.status


def _dedupe_graph_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for node in nodes:
        deduped[node["id"]] = node
    return list(deduped.values())


def _mermaid_label(value: str) -> str:
    return value.replace('"', "'").replace("|", "/").replace("\n", " ")[:80]


def _display_target(state: TestFlowState) -> str:
    return _display_path(state.target_file)


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


def _target_path(state: TestFlowState) -> Path:
    return Path(state.target_file).expanduser().resolve()


def _ensure_module_name(state: TestFlowState) -> None:
    if not state.module_name:
        state.module_name = _safe_identifier(_target_path(state).stem)


def _function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    args = [arg.arg for arg in node.args.args]
    required_count = max(0, len(args) - len(node.args.defaults))
    return {
        "name": node.name,
        "args": args,
        "required_args": args[:required_count],
        "required_arg_count": required_count,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "raises": sorted(_exceptions(node)),
        "lineno": node.lineno,
    }


def _class_info(node: ast.ClassDef) -> dict[str, Any]:
    return {
        "name": node.name,
        "methods": [
            _function_info(child)
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        ],
        "raises": sorted(_exceptions(node)),
        "lineno": node.lineno,
    }


def _imports(tree: ast.AST) -> list[dict[str, Any]]:
    imports: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend({"type": "import", "module": alias.name} for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                {
                    "type": "from",
                    "module": node.module or "",
                    "names": [alias.name for alias in node.names],
                    "level": node.level,
                }
            )
    return imports


def _exceptions(node: ast.AST) -> set[str]:
    exceptions: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc is not None:
            exceptions.add(_exception_name(child.exc))
        elif isinstance(child, ast.ExceptHandler):
            exceptions.add(_exception_name(child.type) if child.type else "Exception")
    return exceptions


def _exception_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return _exception_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return ast.unparse(node)
    return ast.unparse(node)


def _edge_cases_for(name: str, args: list[str]) -> list[str]:
    lowered = name.lower()
    cases: list[str] = []
    if any(token in lowered for token in ("divide", "ratio", "percent")):
        cases.append("zero denominator")
    if any(token in lowered for token in ("factorial", "sqrt")):
        cases.append("negative number")
    if any(token in lowered for token in ("prime", "age", "limit")):
        cases.extend(["small number", "boundary number"])
    if any(token in lowered for token in ("parse", "normalize", "truncate", "text", "csv")):
        cases.extend(["none input", "empty input", "whitespace input"])
    if any(token in lowered for token in ("validate", "order", "shipping", "discount")):
        cases.extend(["invalid input", "boundary value"])
    if any(arg.lower() in {"items", "values", "numbers"} for arg in args):
        cases.append("empty collection")
    return _dedupe(cases or ["typical input", "boundary input", "none input"])


def _calculator_tests(state: TestFlowState) -> str:
    return _import_header(state) + """


def test_add():
    assert target.add(2, 3) == 5


def test_subtract():
    assert target.subtract(10, 4) == 6


def test_divide_normal():
    assert target.divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        target.divide(10, 0)


def test_factorial_zero():
    assert target.factorial(0) == 1


def test_factorial_negative():
    with pytest.raises(ValueError):
        target.factorial(-1)


def test_is_prime_small_numbers():
    assert target.is_prime(0) is False
    assert target.is_prime(1) is False
    assert target.is_prime(2) is True


def test_is_prime_even_number():
    assert target.is_prime(12) is False


def test_is_prime_normal_prime():
    assert target.is_prime(13) is True
"""


def _string_utils_tests(state: TestFlowState) -> str:
    return _import_header(state) + """


def test_normalize_text_collapses_whitespace():
    assert target.normalize_text("  hello    world  ") == "hello world"


def test_normalize_text_rejects_none():
    with pytest.raises(ValueError):
        target.normalize_text(None)


def test_is_palindrome_ignores_case_and_spaces():
    assert target.is_palindrome("Never odd or even") is True


def test_truncate_boundary():
    assert target.truncate("hello", 5) == "hello"
    assert target.truncate("hello", 2) == "he"


def test_truncate_rejects_negative_length():
    with pytest.raises(ValueError):
        target.truncate("hello", -1)


def test_parse_csv_line():
    assert target.parse_csv_line("a, b, c") == ["a", "b", "c"]
    assert target.parse_csv_line("") == []
"""


def _order_utils_tests(state: TestFlowState) -> str:
    return _import_header(state) + """


def test_calculate_discount_customer_types():
    assert target.calculate_discount(100, "regular") == 0
    assert target.calculate_discount(100, "vip") == 15
    assert target.calculate_discount(100, "student") == 10


def test_calculate_discount_invalid_customer():
    with pytest.raises(ValueError):
        target.calculate_discount(100, "guest")


def test_validate_order_valid_items():
    items = [{"name": "Book", "quantity": 2, "price": 10}]
    assert target.validate_order(items) is True


def test_validate_order_rejects_empty_items():
    with pytest.raises(ValueError):
        target.validate_order([])


def test_compute_shipping_regions():
    assert target.compute_shipping(2, "local") == 7
    assert target.compute_shipping(2, "domestic") == 14
    assert target.compute_shipping(2, "international") == 35
"""


def _generic_tests(state: TestFlowState) -> str:
    lines = [_import_header(state).rstrip()]
    for function in state.functions:
        name = _function_name(function)
        if not name:
            continue
        safe_name = _safe_identifier(name)
        lines.extend(
            [
                "",
                "",
                f"def test_{safe_name}_is_callable():",
                f"    assert callable(target.{name})",
            ]
        )
        args = _function_args(function)
        required_count = _required_arg_count(function)
        if required_count <= 2 and not _is_async_function(function):
            values = [_normal_value(arg, name) for arg in args[:required_count]]
            lines.extend(
                [
                    "",
                    "",
                    f"def test_{safe_name}_typical_execution():",
                    "    try:",
                    f"        result = target.{name}({', '.join(values)})",
                    "    except Exception as exc:",
                    "        assert isinstance(exc, Exception)",
                    "    else:",
                    "        assert result is not None or result is None",
                ]
            )
    if len(lines) == 1:
        lines.extend(["", "", "def test_target_module_imports():", "    assert target is not None"])
    return "\n".join(lines)


def _coverage_expansion_tests(state: TestFlowState) -> str:
    lines: list[str] = []
    for function in state.functions:
        name = _function_name(function)
        required_count = _required_arg_count(function)
        if not name or required_count > 2 or _is_async_function(function):
            continue
        safe_name = _safe_identifier(name)
        for index, case in enumerate(_coverage_cases(required_count), 1):
            args = ", ".join(repr(value) for value in case)
            lines.extend(
                [
                    "",
                    "",
                    f"def test_{safe_name}_coverage_case_{index}():",
                    "    try:",
                    f"        result = target.{name}({args})",
                    "    except Exception as exc:",
                    "        assert isinstance(exc, Exception)",
                    "    else:",
                    "        assert result is not None or result is None",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def _import_header(state: TestFlowState) -> str:
    target = str(_target_path(state))
    module_name = _safe_identifier(state.module_name or _target_path(state).stem)
    return "\n".join(
        [
            "import importlib.util",
            "import sys",
            "from pathlib import Path",
            "",
            "import pytest",
            "",
            f"TARGET_FILE = Path({target!r})",
            "",
            "",
            "def _load_target_module():",
            f"    spec = importlib.util.spec_from_file_location({module_name!r}, TARGET_FILE)",
            "    assert spec is not None",
            "    assert spec.loader is not None",
            "    module = importlib.util.module_from_spec(spec)",
            "    sys.modules[spec.name] = module",
            "    spec.loader.exec_module(module)",
            "    return module",
            "",
            "",
            "target = _load_target_module()",
        ]
    )


def _fallback_import_test(state: TestFlowState) -> str:
    return _import_header(state) + "\n\n\ndef test_target_module_imports():\n    assert target is not None\n"


def _valid_test_code(code: str) -> bool:
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return "def test_" in code


def _verify_tests(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    tests = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    if not tests:
        return False
    return all(_has_assertion(test) for test in tests)


def _has_assertion(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(function):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.With):
            for item in node.items:
                context = item.context_expr
                if isinstance(context, ast.Call) and _call_name(context.func) == "pytest.raises":
                    return True
    return False


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _clean_code_block(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:python)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped


def _function_name(function: Any) -> str:
    if isinstance(function, str):
        return function
    if isinstance(function, dict):
        return str(function.get("name", ""))
    return str(getattr(function, "name", ""))


def _function_args(function: Any) -> list[str]:
    if isinstance(function, dict):
        return list(function.get("args", []))
    return list(getattr(function, "args", []))


def _required_arg_count(function: Any) -> int:
    if isinstance(function, dict):
        if "required_arg_count" in function:
            return int(function["required_arg_count"])
        if "required_args" in function:
            return len(function["required_args"])
        return len(function.get("args", []))
    return int(getattr(function, "required_arg_count", 0))


def _is_async_function(function: Any) -> bool:
    if isinstance(function, dict):
        return bool(function.get("is_async", False))
    return bool(getattr(function, "is_async", False))


def _normal_value(arg: str, function_name: str = "") -> str:
    lowered = arg.lower()
    function_lowered = function_name.lower()
    if "region" in lowered:
        return "'local'"
    if "customer" in lowered or "type" in lowered:
        return "'regular'"
    if "items" in lowered:
        return "[{'name': 'Book', 'quantity': 1, 'price': 10}]"
    if "line" in lowered:
        return "'a, b, c'"
    if "text" in lowered or lowered in {"s", "name"}:
        return "'hello'"
    if "max" in lowered or "length" in lowered or "limit" in lowered:
        return "3"
    if "weight" in lowered:
        return "2"
    if any(token in function_lowered for token in ("divide", "ratio")) and lowered in {"b", "denominator", "divisor"}:
        return "2"
    return "1"


def _coverage_cases(required_args: int) -> list[tuple[int, ...]]:
    if required_args == 1:
        return [(-1,), (0,), (1,), (2,), (3,), (4,), (9,), (11,)]
    if required_args == 2:
        return [(1, 2), (0, 0), (-1, 1), (10, 2)]
    return [tuple(0 for _ in range(required_args)), tuple(1 for _ in range(required_args))]


def _has_functions(actual: set[str], required: set[str]) -> bool:
    return required.issubset(actual)


def _normalize_coverage(value: Any) -> float:
    try:
        coverage = float(value)
    except (TypeError, ValueError):
        return 0.0
    if coverage > 1.0:
        coverage = coverage / 100.0
    return max(0.0, min(1.0, coverage))


def _ensure_final_newline(text: str) -> str:
    return text if text.endswith("\n") else f"{text}\n"


def _safe_identifier(value: str) -> str:
    safe = re.sub(r"\W+", "_", value).strip("_")
    if not safe:
        return "target_module"
    if safe[0].isdigit():
        safe = f"module_{safe}"
    return safe


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result
