"""Lightweight project decorator helpers used by repo smoke tests.

These decorators are identity/no-op decorators that mirror the expected
API surface used in `src/fraud_det/crew.py`.
"""
from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


def CrewBase(cls: T) -> T:
    return cls


def agent(fn: Callable[..., object]) -> Callable[..., object]:
    return fn


def task(fn: Callable[..., object]) -> Callable[..., object]:
    return fn


def crew(fn: Callable[..., object]) -> Callable[..., object]:
    return fn
