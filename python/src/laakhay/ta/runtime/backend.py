from __future__ import annotations

import os
from enum import StrEnum


class RuntimeBackend(StrEnum):
    RUST = "rust"
    PYTHON = "python"


def get_runtime_backend() -> RuntimeBackend:
    raw = os.getenv("LAAKHAY_TA_BACKEND", RuntimeBackend.RUST.value).strip().lower()
    # Aggressive beta policy: Rust is the only supported runtime backend.
    # We still parse env for forward compatibility but ignore non-rust modes.
    if raw == RuntimeBackend.RUST.value:
        return RuntimeBackend.RUST
    return RuntimeBackend.RUST


def is_rust_backend() -> bool:
    return get_runtime_backend() == RuntimeBackend.RUST


__all__ = ["RuntimeBackend", "get_runtime_backend", "is_rust_backend"]
