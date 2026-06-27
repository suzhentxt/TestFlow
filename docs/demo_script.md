# TestFlow Demo Script

## 1. Demo Goal

One-shot LLM unit test generation is unreliable because generated tests can have broken imports, weak assertions, missing edge cases, or syntax errors. TestFlow closes the loop by running generated tests, reading real execution feedback, repairing failures, measuring coverage, and expanding tests for uncovered behavior.

This demo proves the full loop: generation -> execution -> repair -> coverage expansion.

## 2. Setup

```bash
pip install -r requirements.txt
```

## 3. Main Demo Command

```bash
python main.py --target examples/calculator.py
```

## 4. Expected Output Shape

```text
========== TestFlow Report ==========
Target: examples/calculator.py
Functions found: 5
Actions taken:
- analyze
- generate_tests
- run_tests
- repair_failed_tests
- measure_coverage
- generate_missing_tests
Final pass rate: 100%
Final coverage: 80%+
Generated tests: generated_tests/test_calculator.py
====================================
```

## 5. What To Say During The Demo

"Most tools stop after generating tests. That is the fragile part: generated tests might not import correctly, might fail for the wrong reason, or might miss important branches."

"TestFlow treats test generation as an execution-guided loop. First it analyzes the target Python file, then it generates pytest tests from the discovered functions and edge cases."

"The important step is that we run pytest. We are not just displaying generated code; we execute it and capture stdout, stderr, return code, and traceback."

"If tests fail, TestFlow uses the traceback to repair the generated test file. That means syntax errors, wrong imports, and incorrect assumptions can be corrected using real runtime feedback."

"After the tests pass, TestFlow measures coverage. If coverage is low, it generates additional tests for uncovered behavior such as exceptions, boundaries, and branches."

"The orchestrator stops only when execution metrics are good enough, then it prints a final report and writes the generated test file."

## 6. Files To Open During Judging

- `examples/calculator.py`
- `generated_tests/test_calculator.py`
- `testflow/orchestrator.py`
- `testflow/runner.py`
- `coverage.xml` or `final_summary.json` if available

## 7. Backup Plan

If the OpenAI API key is unavailable, the API quota is exhausted, or LLM generation fails, use deterministic fallback generation. The fallback should still produce pytest tests for the demo target so the runtime loop can be shown.

Explain this clearly: the engineering contribution is execution-guided orchestration, not only the model call. Even with fallback generation, TestFlow still demonstrates the core loop: analyze source code, generate tests, run pytest, observe failures, repair, measure coverage, and generate more tests when coverage is low.

## 8. 30-Second Emergency Demo

"TestFlow is an execution-guided unit test orchestrator for Python. Instead of doing one-shot `Code -> LLM -> Tests`, it generates pytest tests, runs them, reads failures, repairs using traceback, measures coverage, and adds tests for uncovered behavior."

```bash
python main.py --target examples/calculator.py
```

"The final report shows the actions taken, pass rate, coverage, and generated test file. That is the key idea: the orchestrator makes decisions from real runtime feedback."
