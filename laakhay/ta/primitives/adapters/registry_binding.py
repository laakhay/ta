"""Registry-to-kernel binding helpers for incremental execution."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..kernels.atr import ATRKernel
from ..kernels.ema import EMAKernel
from ..kernels.rolling import RollingMeanKernel, RollingStdKernel, RollingSumKernel
from ..kernels.rsi import RSIKernel


def resolve_kernel_for_indicator(name: str) -> Any | None:
    if name in ("rolling_sum", "sum"):
        return RollingSumKernel()
    if name in ("rolling_mean", "mean", "average", "avg", "sma"):
        return RollingMeanKernel()
    if name in ("rolling_std", "std", "stddev"):
        return RollingStdKernel()
    if name in ("rolling_ema", "ema"):
        return EMAKernel()
    if name == "rsi":
        return RSIKernel()
    if name == "atr":
        return ATRKernel()
    return None


def coerce_incremental_input(name: str, input_val: Any, tick: dict[str, Any], algorithm_state: Any) -> Any:
    """Apply indicator-specific input adaptation outside backend loop."""
    if name != "atr":
        return input_val

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
