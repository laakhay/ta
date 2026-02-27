"""Compatibility shim for legacy incremental backend import path."""

from __future__ import annotations

from .incremental_rust import IncrementalRustBackend


class IncrementalBackend(IncrementalRustBackend):
    """Legacy name retained temporarily; implementation is Rust-backed."""

