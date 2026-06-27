"""Coverage helpers for generated TestFlow tests."""

from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def run_coverage(target_file: str, test_file: str, cwd: str | None = None) -> dict:
    """Run tests with coverage and return line coverage from coverage.xml."""
    working_dir = Path(cwd).resolve() if cwd else Path.cwd()
    target_path = _resolve_path(target_file, working_dir)
    test_path = _resolve_path(test_file, working_dir)
    if _looks_like_test_file(target_path) and not _looks_like_test_file(test_path):
        target_path, test_path = test_path, target_path
    xml_path = working_dir / "coverage.xml"
    _remove_previous_xml(xml_path)
    cov_value = _cov_value(target_path, working_dir)

    result = _run_pytest_cov(test_path, cov_value, working_dir)
    if not xml_path.exists():
        fallback = _run_coverage_py(test_path, target_path, working_dir, xml_path)
        result = _combine_results(result, fallback)

    coverage = _parse_target_line_rate(xml_path, target_path)
    if coverage is None:
        coverage = _parse_line_rate(xml_path)
    if coverage is None:
        coverage = 0.0

    return {
        "coverage": coverage,
        "coverage_percent": coverage * 100.0,
        "xml_path": str(xml_path) if xml_path.exists() else None,
        "stdout": result.stdout or "",
        "stderr": result.stderr or "",
        "returncode": result.returncode,
    }


def _run_pytest_cov(test_path: Path, cov_value: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(test_path),
            f"--cov={cov_value}",
            "--cov-report=xml",
            "--cov-report=term",
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _remove_previous_xml(xml_path: Path) -> None:
    try:
        xml_path.unlink()
    except FileNotFoundError:
        return
    except OSError:
        return


def _run_coverage_py(
    test_path: Path,
    target_path: Path,
    cwd: Path,
    xml_path: Path,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["COVERAGE_FILE"] = str(cwd / ".coverage")

    erase = subprocess.run(
        [sys.executable, "-m", "coverage", "erase"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--source",
            str(target_path.parent),
            "-m",
            "pytest",
            str(test_path),
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    xml = subprocess.run(
        [sys.executable, "-m", "coverage", "xml", "-o", str(xml_path)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    stdout = "\n".join(part for part in (erase.stdout, run.stdout, xml.stdout) if part)
    stderr = "\n".join(part for part in (erase.stderr, run.stderr, xml.stderr) if part)
    returncode = run.returncode if run.returncode != 0 else xml.returncode
    return subprocess.CompletedProcess(run.args, returncode, stdout, stderr)


def _combine_results(
    primary: subprocess.CompletedProcess[str],
    fallback: subprocess.CompletedProcess[str],
) -> subprocess.CompletedProcess[str]:
    stdout = "\n".join(part for part in (primary.stdout, fallback.stdout) if part)
    stderr = "\n".join(part for part in (primary.stderr, fallback.stderr) if part)
    return subprocess.CompletedProcess(fallback.args, fallback.returncode, stdout, stderr)


def _parse_line_rate(xml_path: Path) -> float | None:
    if not xml_path.exists():
        return None
    try:
        root = ET.parse(xml_path).getroot()
        return _normalize_coverage(root.attrib.get("line-rate"))
    except (ET.ParseError, OSError):
        return None


def _parse_target_line_rate(xml_path: Path, target_path: Path) -> float | None:
    if not xml_path.exists():
        return None

    try:
        root = ET.parse(xml_path).getroot()
    except (ET.ParseError, OSError):
        return None

    target_names = _target_xml_filenames(root, target_path)
    for class_node in root.findall(".//class"):
        filename = _normalize_xml_path(class_node.attrib.get("filename", ""))
        if filename in target_names:
            return _normalize_coverage(class_node.attrib.get("line-rate"))

    return None


def _target_xml_filenames(root: ET.Element, target_path: Path) -> set[str]:
    names = {_normalize_xml_path(target_path.name)}

    for source_node in root.findall(".//source"):
        source_text = source_node.text or ""
        if not source_text:
            continue
        try:
            relative = target_path.relative_to(Path(source_text).resolve())
        except ValueError:
            continue
        names.add(_normalize_xml_path(str(relative)))

    return names


def _normalize_xml_path(value: str) -> str:
    return value.replace("\\", "/")


def _normalize_coverage(value: str | None) -> float:
    try:
        coverage = float(value or 0.0)
    except ValueError:
        return 0.0
    return max(0.0, min(1.0, coverage))


def _resolve_path(path: str, cwd: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return candidate.resolve()


def _cov_value(target_path: Path, cwd: Path) -> str:
    module = _module_name(target_path, cwd)
    if module:
        return module
    return str(target_path.parent)


def _module_name(target_path: Path, cwd: Path) -> str:
    if target_path.suffix != ".py":
        return ""
    try:
        relative = target_path.with_suffix("").relative_to(cwd)
    except ValueError:
        return ""

    parts = relative.parts
    if not parts or not all(part.isidentifier() for part in parts):
        return ""
    return ".".join(parts)


def _looks_like_test_file(path: Path) -> bool:
    return path.name.startswith("test_") or path.name.endswith("_test.py")
