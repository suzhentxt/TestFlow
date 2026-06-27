# TestFlow Pitch

Track: Track 2 — Engineering Depth

## 1. 30-Second Pitch

One-shot LLM unit test generation often misses edge cases, creates failing tests, or produces weak assertions that do not validate behavior. TestFlow fixes that by turning test generation into a runtime feedback loop: it generates pytest tests, runs them, observes failures, repairs using traceback, measures coverage, and generates more tests for uncovered behavior.

Our technical claim is simple: unit test generation should be treated as execution-guided search, not one-shot text generation.

## 2. 2-Minute Pitch

### Problem

Engineering teams need more useful unit tests, especially for codebases where behavior is spread across edge cases, validation rules, and legacy assumptions. LLMs can help draft tests, but a generated test file is not valuable until it actually runs and checks meaningful behavior.

### Why One-Shot Generation Fails

The common approach is `Code -> LLM -> Tests`. That skips the most important engineering signal: execution. Without running tests, the system cannot know whether imports are broken, assertions are wrong, exception behavior is missing, or coverage is concentrated only on happy paths.

### How TestFlow Works

TestFlow uses an orchestrated loop. It analyzes a Python target file, generates pytest tests, runs pytest, captures stdout, stderr, return code, and traceback, then updates state. If the tests fail, it repairs them using traceback feedback. If coverage is low, it generates additional tests for missing branches and boundary behavior. Finally, it prints an execution report with pass rate, coverage, actions taken, and the generated test file.

### Engineering Depth

The core contribution is not a chatbot interface. It is a state-based runtime system for test improvement. The orchestrator selects the next action based on real signals: failing tests trigger repair, low coverage triggers expansion, and good execution metrics trigger stop conditions. That makes the workflow measurable and debuggable.

### Demo Explanation

In the demo, we run:

```bash
python main.py --target examples/calculator.py
```

The important part is not only that a test file appears. The important part is the sequence: analyze source, generate tests, run pytest, repair failures if needed, measure coverage, expand tests, and produce a final report.

### Vietnam Impact

Vietnam has many software outsourcing and product engineering teams maintaining large codebases. TestFlow can help improve unit test coverage, reduce manual QA burden, and train junior developers through concrete generated test examples.

### Future Direction

The next version can replace simple heuristics with a learned planner or reward-guided search policy. Instead of fixed thresholds, the system could optimize for pass rate, line coverage, branch coverage, assertion quality, runtime cost, and historical defect patterns.

## 3. Engineering Depth Talking Points

- state-based orchestration
- pytest runner integration
- traceback-guided repair
- coverage-guided generation
- dynamic next-action selection
- final execution report
- future learned planner or reward-guided search

## 4. Codex Angle

We use Codex not only to write code, but to build an execution-aware coding workflow. The system can reason over code, generate tests, run commands, inspect failures, and iterate. Codex helps implement the loop, while TestFlow demonstrates the engineering pattern: generation becomes more reliable when it is grounded in runtime evidence.

## 5. Vietnam Impact

Vietnam has many software outsourcing and product engineering teams maintaining large codebases. TestFlow can help improve unit test coverage, reduce manual QA burden, and train junior developers through concrete generated test examples.

## 6. What Not To Say

- "This fully solves unit testing."
- "This is just a multi-agent system."
- "Coverage means correctness."
- "No human review is needed."

## 7. Strong Final Line

"TestFlow does not just ask an LLM to write tests. It runs them, learns from execution, and improves the suite."
