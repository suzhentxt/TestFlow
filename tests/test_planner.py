from testflow.orchestrator import HeuristicPlanner
from testflow.state import Action, TestFlowState


def _choose(state: TestFlowState) -> Action:
    action, _reason = HeuristicPlanner().choose_next_action(state)
    return action


def test_empty_state_analyzes_first():
    state = TestFlowState(target_file="examples/calculator.py")

    assert _choose(state) == Action.ANALYZE


def test_source_loaded_without_edge_cases_finds_edge_cases():
    state = TestFlowState(target_file="examples/calculator.py")
    state.source_code = "def add(a, b): return a + b"
    state.functions = ["add"]
    state.status = "analyzed"

    assert _choose(state) == Action.FIND_EDGE_CASES


def test_edge_cases_found_without_tests_generates_tests():
    state = TestFlowState(target_file="examples/calculator.py")
    state.source_code = "def add(a, b): return a + b"
    state.functions = ["add"]
    state.edge_cases = {"add": ["negative numbers"]}
    state.status = "edge_cases_found"

    assert _choose(state) == Action.GENERATE_TESTS


def test_generated_tests_are_run():
    state = TestFlowState(target_file="examples/calculator.py")
    state.source_code = "def add(a, b): return a + b"
    state.functions = ["add"]
    state.edge_cases = {"add": ["negative numbers"]}
    state.generated_tests = "def test_add():\n    assert True\n"
    state.has_tests = True
    state.status = "tests_generated"

    assert _choose(state) == Action.RUN_TESTS


def test_failed_tests_trigger_repair():
    state = TestFlowState(target_file="examples/calculator.py")
    state.source_code = "def add(a, b): return a + b"
    state.functions = ["add"]
    state.edge_cases = {"add": ["negative numbers"]}
    state.generated_tests = "def test_add():\n    assert False\n"
    state.total_tests = 3
    state.failed = 1
    state.pass_rate = 0.66
    state.status = "tests_failed"

    assert _choose(state) == Action.REPAIR_TESTS


def test_passing_tests_measure_coverage_when_missing():
    state = TestFlowState(target_file="examples/calculator.py")
    state.source_code = "def add(a, b): return a + b"
    state.functions = ["add"]
    state.edge_cases = {"add": ["negative numbers"]}
    state.generated_tests = "def test_add():\n    assert True\n"
    state.total_tests = 5
    state.passed = 5
    state.pass_rate = 1.0
    state.coverage_measured = False
    state.status = "tests_passed"

    assert _choose(state) == Action.MEASURE_COVERAGE


def test_low_coverage_generates_missing_tests():
    state = TestFlowState(target_file="examples/calculator.py")
    state.source_code = "def add(a, b): return a + b"
    state.functions = ["add"]
    state.edge_cases = {"add": ["negative numbers"]}
    state.generated_tests = "def test_add():\n    assert True\n"
    state.pass_rate = 1.0
    state.coverage_measured = True
    state.coverage = 0.45
    state.coverage_threshold = 0.8
    state.status = "coverage_measured"

    assert _choose(state) == Action.GENERATE_MISSING_TESTS


def test_good_coverage_verifies_tests():
    state = TestFlowState(target_file="examples/calculator.py")
    state.source_code = "def add(a, b): return a + b"
    state.functions = ["add"]
    state.edge_cases = {"add": ["negative numbers"]}
    state.generated_tests = "def test_add():\n    assert True\n"
    state.pass_rate = 1.0
    state.coverage_measured = True
    state.coverage = 0.85
    state.coverage_threshold = 0.8
    state.status = "coverage_measured"

    assert _choose(state) == Action.VERIFY_TESTS


def test_max_iterations_stop():
    state = TestFlowState(target_file="examples/calculator.py")
    state.iterations = state.max_iterations

    assert _choose(state) == Action.STOP
