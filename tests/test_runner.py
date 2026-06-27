from testflow.runner import run_pytest


def test_run_pytest_all_passing(tmp_path):
    test_file = tmp_path / "test_generated.py"
    test_file.write_text(
        "\n".join(
            [
                "def test_one():",
                "    assert 1 == 1",
                "",
                "def test_two():",
                "    assert 'flow'.upper() == 'FLOW'",
                "",
                "def test_three():",
                "    assert len([1, 2, 3]) == 3",
            ]
        ),
        encoding="utf-8",
    )

    result = run_pytest(str(test_file), cwd=str(tmp_path))

    assert result["returncode"] == 0
    assert result["passed"] == 3
    assert result["failed"] == 0
    assert result["errors"] == 0
    assert result["pass_rate"] == 1.0
    assert result["traceback"] == ""


def test_run_pytest_one_failing(tmp_path):
    test_file = tmp_path / "test_generated.py"
    test_file.write_text(
        "\n".join(
            [
                "def test_passes():",
                "    assert True",
                "",
                "def test_fails():",
                "    assert 1 == 2",
            ]
        ),
        encoding="utf-8",
    )

    result = run_pytest(str(test_file), cwd=str(tmp_path))

    assert result["returncode"] != 0
    assert result["passed"] == 1
    assert result["failed"] == 1
    assert result["errors"] == 0
    assert result["pass_rate"] == 0.5
    assert "assert 1 == 2" in result["traceback"]


def test_run_pytest_import_error(tmp_path):
    test_file = tmp_path / "test_generated.py"
    test_file.write_text(
        "import does_not_exist_for_testflow\n\n\ndef test_unreachable():\n    assert True\n",
        encoding="utf-8",
    )

    result = run_pytest(str(test_file), cwd=str(tmp_path))

    assert result["returncode"] != 0
    assert result["passed"] == 0
    assert result["failed"] == 0
    assert result["errors"] == 1
    assert result["pass_rate"] == 0.0
    assert "does_not_exist_for_testflow" in result["traceback"]
