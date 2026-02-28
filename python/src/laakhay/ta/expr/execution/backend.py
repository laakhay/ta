"""Centralized execution backend resolution."""

from __future__ import annotations

import os
from typing import Literal

ExecutionMode = Literal["incremental"]
DEFAULT_EXECUTION_MODE: ExecutionMode = "incremental"


def resolve_execution_mode(mode: str | None = None) -> ExecutionMode:
    selected = (mode or os.environ.get("TA_EXECUTION_MODE", DEFAULT_EXECUTION_MODE)).strip().lower()
    if selected != "incremental":
        raise ValueError(f"Unsupported execution mode '{selected}'. Expected 'incremental'.")
    return selected


def resolve_backend(mode: str | None = None):
    _ = resolve_execution_mode(mode)
    from .backends.incremental_rust import IncrementalRustBackend

    return IncrementalRustBackend()
