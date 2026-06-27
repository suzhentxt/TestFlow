"""Streamlit app for visualizing the TestFlow execution loop."""

import streamlit as st

from demo_data import EXECUTION_TIMELINE, get_demo_generated_tests, get_demo_summary
from utils import (
    build_live_summary,
    format_percent,
    generated_test_path,
    read_text,
    run_testflow_cli,
)


TARGET_FILES = [
    "examples/calculator.py",
    "examples/string_utils.py",
    "examples/order_utils.py",
]


def build_demo_result(target_file):
    """Build deterministic demo-mode UI state."""
    summary = get_demo_summary(target_file)
    return {
        "mode": "Demo Mode",
        "summary": summary,
        "generated_tests": get_demo_generated_tests(target_file),
        "stdout": summary["pytest_stdout"],
        "stderr": summary["pytest_stderr"],
    }


def build_live_result(target_file, max_iterations):
    """Run the CLI and build live-run UI state without crashing the app."""
    cli_result = run_testflow_cli(target_file)
    summary = build_live_summary(target_file, cli_result, max_iterations)
    generated_path = generated_test_path(target_file)
    return {
        "mode": "Live Run",
        "summary": summary,
        "generated_tests": read_text(generated_path),
        "stdout": cli_result.get("stdout", ""),
        "stderr": cli_result.get("stderr", ""),
        "error": cli_result.get("error", ""),
        "generated_path": generated_path,
    }


def render_header():
    """Render the app header."""
    st.title("TestFlow")
    st.caption("Execution-Guided Unit Test Orchestrator")
    st.write("Generate, run, observe, repair, measure coverage, and improve unit tests.")


def render_loop_comparison():
    """Render the one-shot versus TestFlow comparison."""
    st.markdown("### Runtime Loop")
    left, right = st.columns(2)
    with left:
        st.markdown("**Traditional**")
        st.code("Code -> LLM -> Tests", language="text")
    with right:
        st.markdown("**TestFlow**")
        st.code(
            "Generate -> Run -> Observe -> Repair -> Measure Coverage -> Generate More",
            language="text",
        )


def render_metrics(summary):
    """Render pass rate, coverage, iteration, and repair metrics."""
    pass_rate, coverage, iterations, repairs = st.columns(4)
    pass_rate.metric("Pass Rate", format_percent(summary.get("pass_rate")))
    coverage.metric("Coverage", format_percent(summary.get("coverage")))
    iterations.metric("Iterations", summary.get("iterations", "n/a"))
    repairs.metric("Repairs Triggered", summary.get("repairs_triggered", "n/a"))


def render_timeline():
    """Render the execution timeline."""
    st.markdown("### Execution Timeline")
    for index, step in enumerate(EXECUTION_TIMELINE, start=1):
        st.markdown(f"**{index}. {step['title']}**")
        st.caption(step["detail"])


def render_depth_expander():
    """Render engineering-depth talking points."""
    with st.expander("Engineering Depth"):
        st.markdown(
            """
- Stateful orchestration
- Pytest execution loop
- Traceback-guided repair
- Coverage-guided generation
- Runtime-dependent next action
- Future learned planner / reward-guided search
"""
        )


def render_tabs(target_file, result):
    """Render source, generated tests, pytest output, and summary tabs."""
    source_tab, tests_tab, output_tab, summary_tab = st.tabs(
        ["Source Code", "Generated Tests", "Pytest Output", "Final Summary JSON"]
    )

    with source_tab:
        source = read_text(target_file)
        if source is None:
            st.warning(f"{target_file} was not found.")
        else:
            st.code(source, language="python")

    with tests_tab:
        if result["mode"] == "Demo Mode":
            st.code(result["generated_tests"], language="python")
        else:
            generated_tests = result.get("generated_tests")
            generated_path = result.get("generated_path", generated_test_path(target_file))
            if generated_tests:
                st.caption(generated_path)
                st.code(generated_tests, language="python")
            else:
                st.info(f"No generated test file found at {generated_path}.")

    with output_tab:
        st.markdown("**stdout**")
        st.code(result.get("stdout", "") or "(empty)", language="text")
        st.markdown("**stderr**")
        st.code(result.get("stderr", "") or "(empty)", language="text")
        if result.get("error"):
            st.warning(
                "Live Run failed safely. Demo Mode is the reliable public App URL path."
            )

    with summary_tab:
        st.json(result["summary"])


def main():
    """Run the Streamlit app."""
    st.set_page_config(page_title="TestFlow", layout="wide")

    render_header()
    render_loop_comparison()

    with st.sidebar:
        st.header("Run Settings")
        target_file = st.selectbox("Target file", TARGET_FILES)
        st.slider("Coverage target", min_value=0.5, max_value=1.0, value=0.8, step=0.05)
        max_iterations = st.number_input(
            "Max iterations", min_value=1, max_value=10, value=3, step=1
        )
        mode = st.radio("Mode", ["Demo Mode", "Live Run"])
        run_clicked = st.button("Run TestFlow", type="primary", use_container_width=True)

    if run_clicked:
        if mode == "Demo Mode":
            result = build_demo_result(target_file)
        else:
            result = build_live_result(target_file, int(max_iterations))
        st.session_state["testflow_result"] = result
    elif "testflow_result" not in st.session_state:
        st.session_state["testflow_result"] = build_demo_result(target_file)

    result = st.session_state["testflow_result"]
    summary = result["summary"]

    render_metrics(summary)

    if result["mode"] == "Live Run" and summary.get("status") != "success":
        st.info(
            "Live Run depends on the backend runtime and local Python command. "
            "Use Demo Mode for a stable public judging path."
        )

    render_timeline()
    render_depth_expander()
    render_tabs(target_file, result)


if __name__ == "__main__":
    main()
