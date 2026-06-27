"""Run the merged agent layer directly against one target file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.analyzer import AnalyzerAgent
from agents.edge_case import EdgeCaseAgent
from agents.generator import TestGeneratorAgent
from testflow.llm_client import flush_traces


def make_target_importable(test_code: str, target: Path) -> str:
    target_dir = str(target.parent)
    prelude = (
        "import sys\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, r\"{target_dir}\")\n\n"
    )
    if target_dir in test_code:
        return test_code
    return prelude + test_code.lstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test TestFlow agents directly.")
    parser.add_argument("--target", default="examples/calculator.py", help="Target Python file.")
    parser.add_argument(
        "--out",
        default="generated_tests/test_agent_smoke.py",
        help="Where to write generated pytest code.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_file():
        print(f"Error: target file not found: {args.target}")
        return 1

    analysis = AnalyzerAgent().run({"target_file": str(target)})
    edge_cases = EdgeCaseAgent().run({"analysis": analysis})
    test_code = TestGeneratorAgent().run(
        {
            "analysis": analysis,
            "edge_cases": edge_cases,
            "target_file": str(target),
            "source_code": analysis.get("source", ""),
        }
    )
    test_code = make_target_importable(test_code, target)

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(test_code, encoding="utf-8")
    flush_traces()

    print(f"Target: {target}")
    print(f"Functions discovered: {len(analysis.get('functions', []))}")
    print(f"Edge-case groups: {len(edge_cases)}")
    print(f"Generated tests: {output_path}")
    print("LLM mode: real API if OPENAI_API_KEY is set, deterministic fallback otherwise")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
