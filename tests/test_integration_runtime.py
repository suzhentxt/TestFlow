import subprocess
import sys
from pathlib import Path

from testflow.orchestrator import run_testflow
from testflow.state import TestFlowState as RuntimeState


def _write_calculator(tmp_path: Path) -> Path:
    source_file = tmp_path / "calculator.py"
    source_file.write_text(
        "\n".join(
            [
                "def add(a, b): return a + b",
                "def divide(a, b): return a / b",
            ]
        ),
        encoding="utf-8",
    )
    return source_file


def test_run_testflow_generates_and_runs_tests_for_tmp_project(tmp_path):
    source_file = _write_calculator(tmp_path)
    state = RuntimeState(target_file=str(source_file), coverage_target=0.0)

    final_state = run_testflow(state)

    assert Path(final_state.test_file).is_file()
    assert final_state.generated_tests
    assert final_state.pass_rate >= 0.0
    assert final_state.coverage >= 0.0
    assert any(action.startswith("run_pytest") for action in final_state.actions_taken)


def test_main_cli_runs_without_crashing_for_tmp_project(tmp_path):
    source_file = _write_calculator(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    main_path = repo_root / "main.py"

    result = subprocess.run(
        [
            sys.executable,
            str(main_path),
            "--target",
            str(source_file),
            "--coverage-target",
            "0.0",
            "--max-iterations",
            "3",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "TestFlow Runtime Summary" in result.stdout
    assert "Traceback" not in result.stderr
    assert (tmp_path / ".testflow" / "final_summary.json").is_file()


def test_merged_agent_layer_imports():
    from agents.analyzer import AnalyzerAgent
    from agents.coverage_agent import CoverageAgent
    from agents.generator import TestGeneratorAgent
    from agents.repair import RepairAgent
    from agents.verifier import VerifierAgent

    assert AnalyzerAgent
    assert TestGeneratorAgent
    assert RepairAgent
    assert CoverageAgent
    assert VerifierAgent
