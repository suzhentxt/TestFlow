"""Run a real TestFlow agent flow for local target files."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.analyzer import AnalyzerAgent
from agents.edge_case import EdgeCaseAgent
from agents.generator import TestGeneratorAgent
from testflow.llm_client import flush_traces, load_env_file

from run_agent_smoke import make_target_importable


DEFAULT_INPUT_DIR = REPO_ROOT / "test_data"
DEFAULT_GENERATED_DIR = REPO_ROOT / "generated_tests"
DEFAULT_REPORT_DIR = REPO_ROOT / ".testflow"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TestFlow's real agent flow.")
    parser.add_argument("--target", help="One Python file to test. Defaults to all .py files in test_data.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="Folder containing target .py files.")
    parser.add_argument("--generated-dir", default=str(DEFAULT_GENERATED_DIR), help="Folder for generated pytest files.")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Folder for coverage reports.")
    parser.add_argument("--coverage-source", help="Coverage source root. Defaults to the target file parent folder.")
    parser.add_argument("--no-html", action="store_true", help="Skip HTML coverage output.")
    args = parser.parse_args()

    load_env_file()

    targets = _resolve_targets(args.target, Path(args.input_dir))
    if not targets:
        print(f"No target files found. Add .py files to {Path(args.input_dir)} or pass --target <file.py>.", flush=True)
        return 1

    generated_dir = Path(args.generated_dir)
    report_dir = Path(args.report_dir)
    generated_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for target in targets:
        result = run_target(
            target=target,
            generated_dir=generated_dir,
            report_dir=report_dir,
            coverage_source=Path(args.coverage_source).resolve() if args.coverage_source else target.parent,
            html=not args.no_html,
        )
        if result != 0:
            exit_code = result

    return exit_code


def run_target(
    *,
    target: Path,
    generated_dir: Path,
    report_dir: Path,
    coverage_source: Path,
    html: bool,
) -> int:
    target = target.resolve()
    test_file = generated_dir / f"test_{target.stem}_real.py"
    xml_file = report_dir / f"{target.stem}_coverage.xml"
    html_dir = report_dir / "htmlcov" / target.stem

    print("========== TestFlow Real Agent Flow ==========", flush=True)
    print(f"Target: {target}", flush=True)
    print(f"Generated tests: {test_file}", flush=True)
    print(f"Coverage source: {coverage_source}", flush=True)

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
    test_file.write_text(test_code, encoding="utf-8")
    flush_traces()

    print(f"Functions discovered: {len(analysis.get('functions', []))}", flush=True)
    print(f"Edge-case groups: {len(edge_cases)}", flush=True)

    _run([sys.executable, "-m", "coverage", "erase"])
    pytest_result = _run(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            f"--source={coverage_source}",
            "-m",
            "pytest",
            str(test_file),
            "-q",
        ]
    )
    report_result = _run([sys.executable, "-m", "coverage", "report", "-m", str(target)])
    _run([sys.executable, "-m", "coverage", "xml", "-o", str(xml_file)])
    if html:
        _run([sys.executable, "-m", "coverage", "html", "-d", str(html_dir)])

    trace_url = latest_langfuse_trace_url()
    print("============== Flow Artifacts ===============", flush=True)
    print(f"Generated tests: {test_file}", flush=True)
    print(f"Coverage XML: {xml_file}", flush=True)
    if html:
        print(f"Coverage HTML: {html_dir / 'index.html'}", flush=True)
    if trace_url:
        print(f"Langfuse trace: {trace_url}", flush=True)
    print("==============================================", flush=True)

    return pytest_result.returncode or report_result.returncode


def _resolve_targets(target: str | None, input_dir: Path) -> list[Path]:
    if target:
        path = Path(target).resolve()
        return [path] if path.is_file() else []

    input_dir = input_dir.resolve()
    if not input_dir.is_dir():
        return []
    return sorted(path for path in input_dir.rglob("*.py") if path.is_file() and not path.name.startswith("test_"))


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr, flush=True)
    return result


def latest_langfuse_trace_url() -> str:
    try:
        from langfuse import Langfuse
    except Exception:
        return ""

    public_key = _env_secret("LANGFUSE_PUBLIC_KEY")
    secret_key = _env_secret("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        return ""

    try:
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=_langfuse_host(),
        )
        traces = client.api.trace.list(limit=1, name="llm-client-generate")
        if not traces.data:
            return ""
        return client.get_trace_url(trace_id=traces.data[0].id) or ""
    except Exception:
        return ""


def _langfuse_host() -> str:
    host = (os.getenv("LANGFUSE_HOST") or "").strip()
    if not host or host.startswith("replace-with-") or "your-" in host:
        return "https://cloud.langfuse.com"
    return host


def _env_secret(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value or value.startswith("replace-with-") or "your-" in value:
        return ""
    return value


if __name__ == "__main__":
    raise SystemExit(main())
