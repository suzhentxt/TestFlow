class Agent:
    def run(self, state: TestFlowState) -> TestFlowState:
        ...

@dataclass
class TestFlowState:
    target_file: str
    test_file: str
    functions: list
    generated_tests: str
    pytest_stdout: str
    pytest_stderr: str
    traceback: str
    pass_rate: float
    coverage: float
    actions_taken: list[str]
    status: str