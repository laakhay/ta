"""Kernel adapter helpers for runtime bindings."""

from .registry_binding import coerce_incremental_input, resolve_kernel_for_indicator

__all__ = ["resolve_kernel_for_indicator", "coerce_incremental_input"]
