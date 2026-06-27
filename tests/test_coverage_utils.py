from testflow.coverage_utils import run_coverage


def test_run_coverage_reports_positive_line_coverage(tmp_path):
    source_file = tmp_path / "calculator.py"
    source_file.write_text(
        "\n".join(
            [
                "def add(a, b):",
                "    return a + b",
                "",
                "def subtract(a, b):",
                "    return a - b",
            ]
        ),
        encoding="utf-8",
    )
    test_file = tmp_path / "test_calculator.py"
    test_file.write_text(
        "\n".join(
            [
                "from calculator import add",
                "",
                "",
                "def test_add():",
                "    assert add(1, 2) == 3",
            ]
        ),
        encoding="utf-8",
    )

    result = run_coverage(str(source_file), str(test_file), cwd=str(tmp_path))

    assert result["returncode"] == 0
    assert result["coverage"] > 0.0
    assert result["coverage_percent"] > 0.0
    assert result["xml_path"] is not None
