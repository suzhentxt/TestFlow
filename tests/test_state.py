from testflow.state import TestFlowState as RuntimeState


def test_state_defaults_actions_dict_and_summary():
    state = RuntimeState(target_file="src/calculator.py", module_name="calculator")

    state.passed = 2
    state.failed = 1
    state.pass_rate = 2 / 3
    state.coverage = 0.75
    state.add_action("RunTests")

    data = state.to_dict()

    assert data["target_file"] == "src/calculator.py"
    assert data["module_name"] == "calculator"
    assert data["actions_taken"] == ["RunTests"]
    assert data["coverage_target"] == 0.95

    summary = state.summary_text()

    assert "TestFlow Runtime Summary" in summary
    assert "2 passed, 1 failed, 0 errors, 3 total" in summary
    assert "Decision trace:" in summary
