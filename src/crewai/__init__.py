"""Minimal stub for `crewai` for use in test/smoke test environments.

This module provides lightweight Agent/Crew/Task/Process classes when the real
`crewai` package is not installed. It allows smoke tests to run without the full
dependency, validating crew wiring and configs in isolation.

In production, install the real `crewai` package (pip install crewai) which will
override this stub.
"""
from __future__ import annotations

import sys
import os
from typing import Any, Iterable

# Only provide stub if real crewai is not available
_STUB_MODE = "crewai" not in sys.modules or os.environ.get("CREWAI_STUB_MODE", "").lower() in ("1", "true", "yes")


class Agent:
    """Lightweight Agent stub for testing/smoke tests.
    
    When real crewai is installed, this is overridden by the actual Agent class.
    """
    def __init__(self, config: Any = None, verbose: bool = False, **kwargs):
        self.config = config
        self.verbose = verbose
        self._extra = kwargs


class Task:
    """Lightweight Task stub for testing/smoke tests.
    
    When real crewai is installed, this is overridden by the actual Task class.
    """
    def __init__(self, config: Any = None, output_file: str | None = None, **kwargs):
        self.config = config
        self.output_file = output_file
        self._extra = kwargs


class Crew:
    """Lightweight Crew stub for testing/smoke tests.
    
    When real crewai is installed, this is overridden by the actual Crew class.
    Provides minimal interface for kickoff() and other methods to support smoke tests.
    """
    def __init__(self, agents: Iterable[Agent], tasks: Iterable[Task], process: Any = None, verbose: bool = False, **kwargs):
        self.agents = list(agents)
        self.tasks = list(tasks)
        self.process = process
        self.verbose = verbose
        self._extra = kwargs

    def kickoff(self, inputs: dict[str, Any] | None = None, **kwargs) -> str:
        """Stub kickoff that returns a dummy success message."""
        return "Stub crew execution completed successfully."

    def train(self, n_iterations: int = 1, filename: str | None = None, inputs: dict[str, Any] | None = None, **kwargs) -> str:
        """Stub train that returns a dummy message."""
        return f"Stub training completed ({n_iterations} iterations)."

    def replay(self, task_id: str | None = None, **kwargs) -> str:
        """Stub replay that returns a dummy message."""
        return f"Stub replay completed for task {task_id}."

    def test(self, n_iterations: int = 1, eval_llm: str | None = None, inputs: dict[str, Any] | None = None, **kwargs) -> str:
        """Stub test that returns a dummy message."""
        return f"Stub test completed ({n_iterations} iterations)."


class Process:
    """Process constants for crew execution."""
    sequential = "sequential"
    hierarchical = "hierarchical"


__all__ = ["Agent", "Task", "Crew", "Process"]
