"""Package-level compatibility wrapper for the merged LLM client."""

from __future__ import annotations

from llm_client import (
    LLMClient,
    clean_code_block,
    flush_traces,
    load_env_file,
    trace_span,
    update_current_span,
    update_current_trace,
)

__all__ = [
    "LLMClient",
    "clean_code_block",
    "flush_traces",
    "load_env_file",
    "trace_span",
    "update_current_span",
    "update_current_trace",
]
