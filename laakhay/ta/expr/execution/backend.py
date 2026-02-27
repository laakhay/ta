"""Centralized execution backend resolution."""

from __future__ import annotations

import os
from typing import Literal

ExecutionMode = Literal["batch", "incremental"]
IncrementalBackendMode = Literal["rust", "python"]
DEFAULT_EXECUTION_MODE: ExecutionMode = "batch"
DEFAULT_INCREMENTAL_BACKEND: IncrementalBackendMode = "rust"


def resolve_execution_mode(mode: str | None = None) -> ExecutionMode:
    selected = (mode or os.environ.get("TA_EXECUTION_MODE", DEFAULT_EXECUTION_MODE)).strip().lower()
    if selected not in ("batch", "incremental"):
        raise ValueError(f"Unsupported execution mode '{selected}'. Expected 'batch' or 'incremental'.")
    return selected


def resolve_incremental_backend_mode(mode: str | None = None) -> IncrementalBackendMode:
    selected = (mode or os.environ.get("TA_INCREMENTAL_BACKEND", DEFAULT_INCREMENTAL_BACKEND)).strip().lower()
    if selected not in ("rust", "python"):
        raise ValueError(f"Unsupported incremental backend '{selected}'. Expected 'rust' or 'python'.")
    return "rust" if selected == "rust" else "python"


def resolve_backend(mode: str | None = None):
    selected = resolve_execution_mode(mode)
    if selected == "incremental":
        incr_backend = resolve_incremental_backend_mode()
        if incr_backend == "python":
            from .backends.incremental import IncrementalBackend

            return IncrementalBackend()
        from .backends.incremental_rust import IncrementalRustBackend

        return IncrementalRustBackend()

    from .backends.batch import BatchBackend

    return BatchBackend()
