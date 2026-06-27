# Session Handoff

## Current Working State

- Repo root: `D:\TestFlow`.
- Runtime demo command: `python main.py --target examples/calculator.py`.
- Windows baseline command: `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1`.
- Bash baseline command: `./init.sh`, currently blocked on this machine because WSL has no installed distro.
- Python commands should run through `.venv`; in Codex sandbox, `.venv` Python needs escalation because its base interpreter is under `C:\Users`.

## Runtime Engine Status

- Implemented runtime files:
  - `main.py`
  - `testflow/state.py`
  - `testflow/runner.py`
  - `testflow/coverage_utils.py`
  - `testflow/orchestrator.py`
- Demo target: `examples/calculator.py`.
- Generated tests are written to root `generated_tests/test_<module>.py`.
- Final report JSON is written to `.testflow/final_summary.json`.
- `.testflow/` and generated test files are ignored so live demos do not dirty the repo.

## Verified Commands

- `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1` -> pass, 7 tests.
- `D:\TestFlow\.venv\Scripts\python.exe -m pytest tests` -> 7 passed.
- `D:\TestFlow\.venv\Scripts\python.exe main.py --target examples\calculator.py` -> exit 0, pass rate 100%, target-file coverage 100%, generated file `generated_tests/test_calculator.py`.
- `bash ./init.sh` -> fails because WSL has no installed distro.

## Known Gaps

- No `pyproject.toml` yet.
- No installable console script yet; do not use `testflow run` until `tf-001` is completed.
- Agent layer remains teammate-owned. The orchestrator uses deterministic fallbacks when agent imports are unavailable.
- Coverage currently reports target-file line coverage, not whole-example-directory coverage.

## Recommended Next Step

Finish `tf-001`: add an installable Python package skeleton and console entry point so `testflow --help` and eventually `testflow run ...` work from `.venv`.
