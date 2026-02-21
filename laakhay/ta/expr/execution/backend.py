"""Centralized execution backend resolution."""

from __future__ import annotations

import os
from typing import Literal

ExecutionMode = Literal["batch", "incremental"]
DEFAULT_EXECUTION_MODE: ExecutionMode = "batch"


def resolve_execution_mode(mode: str | None = None) -> ExecutionMode:
    selected = (mode or os.environ.get("TA_EXECUTION_MODE", DEFAULT_EXECUTION_MODE)).strip().lower()
    if selected not in ("batch", "incremental"):
        raise ValueError(f"Unsupported execution mode '{selected}'. Expected 'batch' or 'incremental'.")
    return selected


def resolve_backend(mode: str | None = None):
    selected = resolve_execution_mode(mode)
    if selected == "incremental":
        from ..runtime.backends.incremental import IncrementalBackend

        return IncrementalBackend()

    from ..runtime.backends.batch import BatchBackend

    return BatchBackend()
