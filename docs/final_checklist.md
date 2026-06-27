# Final Submission Checklist

Project: TestFlow — Execution-Guided Unit Test Orchestrator for Python  
Track: Track 2 — Engineering Depth

Use this in the final 10 minutes before submission.

## 1. Repository Files

Confirm these files exist:

- [ ] `README.md`
- [ ] `requirements.txt`
- [ ] `.gitignore`
- [ ] `examples/calculator.py`
- [ ] `examples/string_utils.py`
- [ ] `examples/order_utils.py`
- [ ] `docs/demo_script.md`
- [ ] `docs/pitch.md`
- [ ] `generated_tests/.gitkeep`

## 2. Demo Command

Confirm this command is visible and ready to run:

```bash
python main.py --target examples/calculator.py
```

## 3. Expected Generated Output

After running the demo, check:

- [ ] `generated_tests/test_calculator.py` exists
- [ ] final report is printed
- [ ] pass rate is shown
- [ ] coverage is shown if runtime supports it

## 4. Files To Show Judges

Have these files ready to open:

- [ ] `README.md`
- [ ] `examples/calculator.py`
- [ ] `generated_tests/test_calculator.py`
- [ ] `testflow/orchestrator.py`
- [ ] `testflow/runner.py`
- [ ] `docs/pitch.md`

## 5. Engineering Depth Talking Points

Use these points during judging:

- this is not one-shot generation
- this is not a chatbot
- tests are actually executed
- traceback guides repair
- coverage guides generation
- orchestrator is state-based
- future learned planner is possible

## 6. Emergency Fallback

If the live demo breaks:

- [ ] open README architecture
- [ ] open `docs/demo_script.md`
- [ ] open generated test file if available
- [ ] explain deterministic fallback
- [ ] emphasize runtime loop

## 7. Final Submit Checks

Before submitting:

- [ ] GitHub repo is public
- [ ] README renders correctly
- [ ] Mermaid diagram renders correctly
- [ ] no `.env` file committed
- [ ] no API key committed
- [ ] requirements are minimal
- [ ] demo command is visible in README
