"""Deterministic demo data for the TestFlow Streamlit app."""

CALCULATOR_TARGET = "examples/calculator.py"

TARGET_FUNCTIONS = {
    "examples/calculator.py": ["add", "subtract", "divide", "factorial", "is_prime"],
    "examples/string_utils.py": [
        "normalize_text",
        "is_palindrome",
        "truncate",
        "parse_csv_line",
    ],
    "examples/order_utils.py": [
        "calculate_discount",
        "validate_order",
        "compute_shipping",
    ],
}

DEMO_SUMMARY = {
    "target_file": "examples/calculator.py",
    "functions": ["add", "subtract", "divide", "factorial", "is_prime"],
    "actions_taken": [
        "analyze",
        "generate_tests",
        "run_tests",
        "repair_failed_tests",
        "run_tests_again",
        "measure_coverage",
        "generate_missing_tests",
        "final_report",
    ],
    "pass_rate": 1.0,
    "coverage": 0.96,
    "iterations": 3,
    "repairs_triggered": 1,
    "generated_tests_count": 9,
    "pytest_stdout": "9 passed in 0.42s",
    "pytest_stderr": "",
    "status": "success",
}

EXECUTION_TIMELINE = [
    {
        "title": "Analyze source code",
        "detail": "Read the target file and extract functions, signatures, and visible branches.",
    },
    {
        "title": "Generate pytest tests",
        "detail": "Create initial tests for normal paths and obvious edge cases.",
    },
    {
        "title": "Run pytest",
        "detail": "Execute the generated suite and capture stdout, stderr, and return code.",
    },
    {
        "title": "Observe runtime feedback",
        "detail": "Use failures, tracebacks, pass rate, and coverage as state updates.",
    },
    {
        "title": "Repair failed tests using traceback",
        "detail": "Fix broken imports, syntax mistakes, and wrong generated assumptions.",
    },
    {
        "title": "Run pytest again",
        "detail": "Verify that repairs improved the generated suite.",
    },
    {
        "title": "Measure coverage",
        "detail": "Measure line coverage for the target module after tests pass.",
    },
    {
        "title": "Generate tests for missing coverage",
        "detail": "Add tests for uncovered branches, exceptions, and boundaries.",
    },
    {
        "title": "Final report",
        "detail": "Report actions taken, pass rate, coverage, and generated test path.",
    },
]

CALCULATOR_GENERATED_TESTS = '''"""Generated pytest tests for examples/calculator.py."""

import pytest

from examples.calculator import add, subtract, divide, factorial, is_prime


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(10, 4) == 6


def test_divide_normal():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)


def test_factorial_zero():
    assert factorial(0) == 1


def test_factorial_negative():
    with pytest.raises(ValueError):
        factorial(-1)


def test_is_prime_small_numbers():
    assert is_prime(0) is False
    assert is_prime(1) is False
    assert is_prime(2) is True


def test_is_prime_even_number():
    assert is_prime(12) is False


def test_is_prime_normal_prime():
    assert is_prime(13) is True
'''

STRING_GENERATED_TESTS = '''"""Generated pytest tests for examples/string_utils.py."""

import pytest

from examples.string_utils import is_palindrome, normalize_text, parse_csv_line, truncate


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  hello    world  ") == "hello world"


def test_normalize_text_rejects_none():
    with pytest.raises(ValueError):
        normalize_text(None)


def test_is_palindrome_ignores_case_and_spaces():
    assert is_palindrome("Never odd or even") is True


def test_truncate_boundary():
    assert truncate("hello", 5) == "hello"
    assert truncate("hello", 2) == "he"


def test_parse_csv_line():
    assert parse_csv_line("a, b, c") == ["a", "b", "c"]
'''

ORDER_GENERATED_TESTS = '''"""Generated pytest tests for examples/order_utils.py."""

import pytest

from examples.order_utils import calculate_discount, compute_shipping, validate_order


def test_calculate_discount_vip():
    assert calculate_discount(100, "vip") == 15


def test_calculate_discount_unknown_customer():
    with pytest.raises(ValueError):
        calculate_discount(100, "guest")


def test_validate_order_valid_items():
    items = [{"name": "Book", "quantity": 2, "price": 10}]
    assert validate_order(items) is True


def test_validate_order_empty_items():
    with pytest.raises(ValueError):
        validate_order([])


def test_compute_shipping_international():
    assert compute_shipping(2, "international") == 35
'''

DEMO_TESTS_BY_TARGET = {
    "examples/calculator.py": CALCULATOR_GENERATED_TESTS,
    "examples/string_utils.py": STRING_GENERATED_TESTS,
    "examples/order_utils.py": ORDER_GENERATED_TESTS,
}


def get_demo_summary(target_file):
    """Return deterministic summary data for a selected target file."""
    summary = dict(DEMO_SUMMARY)
    summary["target_file"] = target_file
    summary["functions"] = TARGET_FUNCTIONS.get(target_file, [])
    if target_file != CALCULATOR_TARGET:
        summary["coverage"] = 0.96
        summary["generated_tests_count"] = 5
        summary["pytest_stdout"] = "5 passed in 0.31s"
    return summary


def get_demo_generated_tests(target_file):
    """Return deterministic generated pytest code for a selected target file."""
    return DEMO_TESTS_BY_TARGET.get(target_file, CALCULATOR_GENERATED_TESTS)
