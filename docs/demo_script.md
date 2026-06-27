# TestFlow Demo Script

## 1. Demo Goal

One-shot LLM unit test generation is unreliable because generated tests can have broken imports, weak assertions, missing edge cases, or syntax errors. TestFlow closes the loop by running generated tests, reading real execution feedback, repairing failures, measuring coverage, and expanding tests for uncovered behavior.

This demo proves the full loop: generation -> execution -> repair -> coverage expansion.

## 2. Streamlit App Judging Flow

Use this 5-minute flow when judges ask for a public App URL:

1. Open the Streamlit App URL: https://testflow-uet.streamlit.app/
2. Select `Demo Mode` in the sidebar.
3. Click `Run TestFlow`.
4. Show the metrics: pass rate, coverage, iterations, and repairs triggered.
5. Walk through the execution timeline: analyze, generate, run, observe, repair, measure coverage, generate missing tests, final report.
6. Open the `Generated Tests` tab and point out pytest cases for normal behavior, exceptions, and boundary inputs.
7. Open the `Final Summary JSON` tab to show the state-based execution result.
8. If judges ask about implementation depth, open the GitHub code for `testflow/orchestrator.py`, `testflow/runner.py`, and `README.md`.
9. If the app fails, fall back to the CLI command below.

## 3. Setup

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1
```

Run the Streamlit UI locally:

```bash
streamlit run ui/app.py
```

## 4. Main Demo Command

```bash
python main.py --target examples/calculator.py --coverage-threshold 0.95 --max-iterations 12
```

## 5. Expected Output Shape

```text
========== TestFlow Report ==========
TestFlow Runtime Summary
Target: examples/calculator.py
Generated test file: generated_tests/test_calculator.py

Decision trace:
[0] initialized -> analyze
    reason: source code not loaded
[1] analyzed -> find_edge_cases
    reason: edge cases not discovered
[2] edge_cases_found -> generate_tests
    reason: no tests generated
[3] tests_generated -> run_tests
    reason: tests need execution
[4] tests_passed -> measure_coverage
    reason: tests pass but coverage not measured
[5] coverage_measured -> generate_missing_tests
    reason: coverage below threshold

Final metrics:
Pass rate: 100%
Coverage: 100%
Status: success
====================================
```

## 6. What To Say During The Demo

"Most tools stop after generating tests. That is the fragile part: generated tests might not import correctly, might fail for the wrong reason, or might miss important branches."

"TestFlow treats test generation as an execution-guided loop. First it analyzes the target Python file, then it generates pytest tests from the discovered functions and edge cases."

"The important step is that we run pytest. We are not just displaying generated code; we execute it and capture stdout, stderr, return code, and traceback."

"If tests fail, TestFlow uses the traceback to repair the generated test file. That means syntax errors, wrong imports, and incorrect assumptions can be corrected using real runtime feedback."

"After the tests pass, TestFlow measures coverage. If coverage is low, it generates additional tests for uncovered behavior such as exceptions, boundaries, and branches."

"The orchestrator stops only when execution metrics are good enough, then it prints a final report and writes the generated test file."

## 7. Files To Open During Judging

- `examples/calculator.py`
- `generated_tests/test_calculator.py`
- `testflow/orchestrator.py`
- `testflow/runner.py`
- `coverage.xml` or `.testflow/final_summary.json` if available

## 8. Backup Plan

If the OpenAI API key is unavailable, the API quota is exhausted, or LLM generation fails, use deterministic fallback generation. The fallback should still produce pytest tests for the demo target so the runtime loop can be shown.

Explain this clearly: the engineering contribution is execution-guided orchestration, not only the model call. Even with fallback generation, TestFlow still demonstrates the core loop: analyze source code, generate tests, run pytest, observe failures, repair, measure coverage, and generate more tests when coverage is low.

If the Streamlit app fails during judging, use the CLI fallback:

```bash
python main.py --target examples/calculator.py --coverage-threshold 0.95 --max-iterations 12
```

## 9. 30-Second Emergency Demo

"TestFlow is an execution-guided unit test orchestrator for Python. Instead of doing one-shot `Code -> LLM -> Tests`, it generates pytest tests, runs them, reads failures, repairs using traceback, measures coverage, and adds tests for uncovered behavior."

```bash
python main.py --target examples/calculator.py --coverage-threshold 0.95 --max-iterations 12
```

"The final report shows the actions taken, pass rate, coverage, and generated test file. That is the key idea: the orchestrator makes decisions from real runtime feedback."
