"""Helpers for scalar series handling in the expression system."""

from datetime import UTC
from typing import Any

from ...core.series import Series
from ..ir.nodes import SCALAR_SYMBOL


def _make_scalar_series(value: Any) -> Series[Any]:
    """Create a single-point series for a scalar value."""
    from datetime import datetime

    return Series(
        timestamps=(datetime(1970, 1, 1, tzinfo=UTC),),
        values=(value,),
        symbol=SCALAR_SYMBOL,
        timeframe="1s",
        availability_mask=(True,),
    )


def _broadcast_scalar_series(scalar_series: Series[Any], target_series: Series[Any]) -> Series[Any]:
    """Broadcast a scalar series to match the length and metadata of a target series."""
    if scalar_series.symbol != SCALAR_SYMBOL or len(scalar_series) != 1:
        return scalar_series

    value = scalar_series.values[0]
    return Series(
        timestamps=target_series.timestamps,
        values=tuple(value for _ in range(len(target_series))),
        symbol=target_series.symbol,
        timeframe=target_series.timeframe,
        availability_mask=tuple(True for _ in range(len(target_series))),
    )
