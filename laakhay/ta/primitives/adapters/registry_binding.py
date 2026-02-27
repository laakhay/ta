"""Registry-to-kernel binding helpers for incremental execution.

Dispatch is driven by IndicatorSpec.runtime_binding.kernel_id.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from ..kernels.atr import ATRKernel
from ..kernels.rsi import RSIKernel
from ..kernels.stochastic import StochasticKernel

if TYPE_CHECKING:
    from ...registry.models import IndicatorHandle

# kernel_id (from RuntimeBindingSpec) -> Kernel instance
# Aliases share the same kernel; map all registered kernel_ids.
_KERNEL_ID_TO_KERNEL: dict[str, Any] = {
    "rsi": RSIKernel(),
    "atr": ATRKernel(),
    "stochastic": StochasticKernel(),
    # Volume + moving-average families are Rust-batch-backed and intentionally
    # not maintained here for incremental kernel routing.
}


def resolve_kernel_for_indicator(handle: IndicatorHandle) -> Any | None:
    """Resolve kernel from IndicatorSpec.runtime_binding.kernel_id."""
    kernel_id = handle.indicator_spec.runtime_binding.kernel_id
    return _KERNEL_ID_TO_KERNEL.get(kernel_id)


def coerce_incremental_input(kernel_id: str, input_val: Any, tick: dict[str, Any], algorithm_state: Any) -> Any:
    """Apply kernel-specific input adaptation (e.g. ATR needs true range)."""
    if kernel_id == "atr":
        tr = Decimal("0")
        if "high" in tick and "low" in tick:
            high = Decimal(str(tick["high"]))
            low = Decimal(str(tick["low"]))
            tr = high - low
            prev_close = getattr(algorithm_state, "prev_close", None)
            if prev_close is not None:
                tr = max(tr, abs(high - prev_close), abs(low - prev_close))
            algorithm_state.prev_close = Decimal(str(tick["close"])) if "close" in tick else None
        return tr

    if kernel_id == "stochastic":
        if "high" in tick and "low" in tick and "close" in tick:
            return (Decimal(str(tick["high"])), Decimal(str(tick["low"])), Decimal(str(tick["close"])))
        return (Decimal(0), Decimal(0), Decimal(0))

    return input_val
