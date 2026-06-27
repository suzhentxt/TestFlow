"""Command-line entry point for the TestFlow prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from testflow.llm_client import flush_traces
from testflow.orchestrator import run_testflow
from testflow.state import TestFlowState


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TestFlow on a target Python file.")
    parser.add_argument("--target", required=True, help="Path to the target Python file.")
    parser.add_argument(
        "--coverage-threshold",
        "--coverage-target",
        dest="coverage_threshold",
        type=float,
        default=0.8,
        help="Target line coverage from 0.0 to 1.0.",
    )
    parser.add_argument("--max-iterations", type=int, default=8, help="Maximum pytest iterations.")
    args = parser.parse_args(argv)

    target_path = Path(args.target).expanduser()
    if not target_path.is_file():
        print(f"Error: target file not found: {args.target}", file=sys.stderr)
        return 1

    state = TestFlowState(
        target_file=str(target_path.resolve()),
        module_name=target_path.stem,
        coverage_threshold=args.coverage_threshold,
        max_iterations=args.max_iterations,
    )
    final_state = run_testflow(state)

    summary = final_state.summary_text()
    print(summary)

    output_dir = Path(".testflow")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "final_summary.json"
    summary_data = final_state.to_summary_dict()
    summary_data["summary_text"] = summary
    summary_data["raw_state"] = final_state.to_dict()
    summary_path.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    Path("final_summary.json").write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    flush_traces()

    return 0 if final_state.pass_rate == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
