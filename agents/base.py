"""Shared agent interface."""

from __future__ import annotations

from typing import Any


class BaseAgent:
    """Base class for TestFlow agents."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__

    def run(self, state: dict[str, Any]) -> Any:
        raise NotImplementedError

