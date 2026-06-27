"""Run a real TestFlow agent flow for local target files."""

from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.analyzer import AnalyzerAgent
from agents.coverage_agent import CoverageAgent
from agents.edge_case import EdgeCaseAgent
from agents.generator import TestGeneratorAgent
from agents.repair import RepairAgent
from agents.verifier import VerifierAgent
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
    parser.add_argument("--coverage-target", type=float, default=80.0, help="Coverage percent target before applying CoverageAgent.")
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
            coverage_target=args.coverage_target,
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
    coverage_target: float,
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
    print(f"Coverage target: {coverage_target:.1f}%", flush=True)

    tracer = FlowTracer()
    with tracer.observation(
        name="testflow-real-flow",
        as_type="chain",
        input={"target": str(target), "coverage_source": str(coverage_source)},
        metadata={"generated_tests": str(test_file), "report_dir": str(report_dir)},
    ) as flow:
        with tracer.observation(name="analyze-target", as_type="agent", input={"target": str(target)}) as span:
            analysis = AnalyzerAgent().run({"target_file": str(target)})
            span.update(
                output={
                    "functions": [item.get("name") for item in analysis.get("functions", [])],
                    "classes": [item.get("name") for item in analysis.get("classes", [])],
                }
            )

        with tracer.observation(
            name="find-edge-cases",
            as_type="agent",
            input={"function_count": len(analysis.get("functions", []))},
        ) as span:
            edge_cases = EdgeCaseAgent().run({"analysis": analysis})
            span.update(
                output={
                    "edge_case_groups": len(edge_cases),
                    "functions": [item.get("function") for item in edge_cases],
                }
            )

        with tracer.observation(
            name="generate-tests",
            as_type="agent",
            input={
                "target": str(target),
                "functions": [item.get("name") for item in analysis.get("functions", [])],
                "edge_case_groups": len(edge_cases),
            },
        ) as span:
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
            span.update(output={"test_file": str(test_file), "test_code_chars": len(test_code)})

        print(f"Functions discovered: {len(analysis.get('functions', []))}", flush=True)
        print(f"Edge-case groups: {len(edge_cases)}", flush=True)

        flush_traces()

        erase_coverage(tracer, "coverage-erase-initial")
        pytest_result = run_tests_with_coverage(tracer, "run-generated-tests", test_file, coverage_source)

        with tracer.observation(
            name="repair-tests",
            as_type="agent",
            input={
                "test_file": str(test_file),
                "previous_returncode": pytest_result.returncode,
                "applies_only_on_failure": True,
            },
        ) as span:
            current_test_code = test_file.read_text(encoding="utf-8")
            repaired_test_code = RepairAgent().run(
                {
                    "source_code": analysis.get("source", ""),
                    "current_test_code": current_test_code,
                    "pytest_stdout": pytest_result.stdout,
                    "pytest_stderr": pytest_result.stderr,
                    "traceback": pytest_result.stderr or pytest_result.stdout,
                }
            )
            repaired_test_code = make_target_importable(repaired_test_code, target)
            repair_applied = pytest_result.returncode != 0
            if repair_applied:
                test_file.write_text(repaired_test_code, encoding="utf-8")
            span.update(
                output={
                    "applied": repair_applied,
                    "candidate_chars": len(repaired_test_code),
                    "reason": "pytest_failed" if repair_applied else "pytest_already_passing",
                },
            )
        flush_traces()

        if repair_applied:
            erase_coverage(tracer, "coverage-erase-after-repair")
            pytest_result = run_tests_with_coverage(tracer, "run-repaired-tests", test_file, coverage_source)

        report_result, coverage_percent = measure_coverage(tracer, "measure-coverage", target)

        with tracer.observation(
            name="improve-coverage",
            as_type="agent",
            input={
                "target": str(target),
                "coverage_percent": coverage_percent,
                "coverage_target": coverage_target,
                "applies_only_below_target": True,
            },
        ) as span:
            current_test_code = test_file.read_text(encoding="utf-8")
            coverage_test_code = CoverageAgent().run(
                {
                    "source_code": analysis.get("source", ""),
                    "current_tests": current_test_code,
                    "current_coverage": report_result.stdout,
                    "coverage": coverage_percent,
                }
            )
            coverage_test_code = make_target_importable(coverage_test_code, target)
            coverage_applied = pytest_result.returncode == 0 and coverage_percent < coverage_target
            if coverage_applied:
                test_file.write_text(coverage_test_code, encoding="utf-8")
            span.update(
                output={
                    "applied": coverage_applied,
                    "candidate_chars": len(coverage_test_code),
                    "coverage_percent": coverage_percent,
                    "coverage_target": coverage_target,
                    "reason": "coverage_below_target" if coverage_applied else "coverage_target_met_or_tests_failed",
                },
            )
        flush_traces()

        if coverage_applied:
            erase_coverage(tracer, "coverage-erase-after-coverage-agent")
            pytest_result = run_tests_with_coverage(tracer, "run-coverage-expanded-tests", test_file, coverage_source)
            report_result, coverage_percent = measure_coverage(tracer, "measure-coverage-after-coverage-agent", target)

        with tracer.observation(
            name="verify-tests",
            as_type="agent",
            input={"test_file": str(test_file), "pytest_returncode": pytest_result.returncode, "coverage_percent": coverage_percent},
        ) as span:
            verification = VerifierAgent().run({"test_code": test_file.read_text(encoding="utf-8")})
            span.update(
                output={
                    "ok": verification.get("ok"),
                    "issue_count": len(verification.get("issues", [])),
                    "test_count": verification.get("test_count", 0),
                    "issues": verification.get("issues", [])[:10],
                },
                level="WARNING" if not verification.get("ok") else "DEFAULT",
            )

        xml_result, html_result = write_coverage_artifacts(tracer, xml_file, html_dir, html)

        flow.update(
            output={
                "target": str(target),
                "test_file": str(test_file),
                "pytest_returncode": pytest_result.returncode,
                "coverage_percent": coverage_percent,
                "coverage_target": coverage_target,
                "coverage_xml": str(xml_file),
                "coverage_html": str(html_dir / "index.html") if html else "",
                "repair_applied": repair_applied,
                "coverage_agent_applied": coverage_applied,
                "verifier_ok": verification.get("ok"),
            },
            level="ERROR" if pytest_result.returncode or report_result.returncode or xml_result.returncode else "DEFAULT",
        )

    tracer.flush()
    flush_traces()
    trace_url = tracer.trace_url() or latest_langfuse_trace_url("testflow-real-flow")
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


def erase_coverage(tracer: "FlowTracer", name: str) -> subprocess.CompletedProcess[str]:
    with tracer.observation(name=name, as_type="tool"):
        return _run([sys.executable, "-m", "coverage", "erase"])


def run_tests_with_coverage(
    tracer: "FlowTracer",
    name: str,
    test_file: Path,
    coverage_source: Path,
) -> subprocess.CompletedProcess[str]:
    with tracer.observation(
        name=name,
        as_type="tool",
        input={"test_file": str(test_file), "coverage_source": str(coverage_source)},
    ) as span:
        result = _run(
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
        span.update(
            output={
                "returncode": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
            },
            level="ERROR" if result.returncode else "DEFAULT",
        )
        return result


def measure_coverage(
    tracer: "FlowTracer",
    name: str,
    target: Path,
) -> tuple[subprocess.CompletedProcess[str], float]:
    with tracer.observation(name=name, as_type="evaluator", input={"target": str(target)}) as span:
        result = _run([sys.executable, "-m", "coverage", "report", "-m", str(target)])
        coverage_percent = _coverage_percent(result.stdout, target)
        span.update(
            output={
                "returncode": result.returncode,
                "coverage_percent": coverage_percent,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
            level="ERROR" if result.returncode else "DEFAULT",
        )
        return result, coverage_percent


def write_coverage_artifacts(
    tracer: "FlowTracer",
    xml_file: Path,
    html_dir: Path,
    html: bool,
) -> tuple[subprocess.CompletedProcess[str], subprocess.CompletedProcess[str] | None]:
    with tracer.observation(name="write-coverage-artifacts", as_type="tool") as span:
        xml_result = _run([sys.executable, "-m", "coverage", "xml", "-o", str(xml_file)])
        html_result = None
        if html:
            html_result = _run([sys.executable, "-m", "coverage", "html", "-d", str(html_dir)])
        span.update(
            output={
                "xml_file": str(xml_file),
                "html_file": str(html_dir / "index.html") if html else "",
                "xml_returncode": xml_result.returncode,
                "html_returncode": html_result.returncode if html_result else None,
            },
            level="ERROR" if xml_result.returncode or (html_result and html_result.returncode) else "DEFAULT",
        )
        return xml_result, html_result


def _coverage_percent(stdout: str, target: Path) -> float:
    target_name = str(target).replace("/", "\\")
    for line in stdout.splitlines():
        if str(target) in line or target_name in line or target.name in line:
            match = re.search(r"(\d+(?:\.\d+)?)%", line)
            if match:
                return float(match.group(1))
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%", stdout)
    if match:
        return float(match.group(1))
    return 0.0


class FlowTracer:
    def __init__(self) -> None:
        self.client: Any | None = None
        self.last_trace_id = ""
        if not _truthy(os.getenv("LANGFUSE_ENABLED", "true")):
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
            self.client = Langfuse(public_key=public_key, secret_key=secret_key, host=_langfuse_host())
        except Exception:
            self.client = None

    @contextmanager
    def observation(
        self,
        *,
        name: str,
        as_type: str,
        input: Any | None = None,
        output: Any | None = None,
        metadata: Any | None = None,
    ) -> Iterator[Any]:
        if self.client is None:
            with nullcontext(NoopObservation()) as observation:
                yield observation
            return

        with self.client.start_as_current_observation(
            name=name,
            as_type=as_type,
            input=input,
            output=output,
            metadata=metadata,
        ) as observation:
            if not self.last_trace_id:
                try:
                    self.last_trace_id = self.client.get_current_trace_id() or ""
                except Exception:
                    self.last_trace_id = ""
            yield observation

    def trace_url(self) -> str:
        if self.client is None or not self.last_trace_id:
            return ""
        try:
            return self.client.get_trace_url(trace_id=self.last_trace_id) or ""
        except Exception:
            return ""

    def flush(self) -> None:
        if self.client is None:
            return
        try:
            self.client.flush()
        except Exception:
            return


class NoopObservation:
    def update(self, **_: Any) -> "NoopObservation":
        return self


def latest_langfuse_trace_url(name: str = "testflow-real-flow", attempts: int = 5, delay: float = 0.8) -> str:
    try:
        from langfuse import Langfuse
    except Exception:
        return ""

    public_key = _env_secret("LANGFUSE_PUBLIC_KEY")
    secret_key = _env_secret("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        return ""

    try:
        client = Langfuse(public_key=public_key, secret_key=secret_key, host=_langfuse_host())
        for _ in range(attempts):
            traces = client.api.trace.list(limit=1, name=name)
            if traces.data:
                return client.get_trace_url(trace_id=traces.data[0].id) or ""
            time.sleep(delay)
        return ""
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


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
