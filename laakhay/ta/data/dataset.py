"""Dataset helpers shared across TA consumers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from ..core.bar import Bar
from ..core.dataset import Dataset
from ..core.dataset import dataset as _dataset_builder
from ..core.ohlcv import OHLCV

NUMERIC_FIELDS = {"open", "high", "low", "close", "volume"}


def dataset(*args: Any, **kwargs: Any) -> Dataset:
    """Backwards-compatible factory that proxies to core.dataset.dataset."""
    return _dataset_builder(*args, **kwargs)


def _normalize_bar_value(key: str, value: Any) -> Any:
    """Normalize individual bar field values."""
    if key == "timestamp":
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return value
        if isinstance(value, int | float):
            return datetime.fromtimestamp(float(value))
        return value

    if key in NUMERIC_FIELDS:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except (TypeError, ValueError):
                return value
        if isinstance(value, int | float):
            return float(value)
    return value


def dataset_from_bars(
    bars: Sequence[Mapping[str, Any]],
    *,
    symbol: str,
    timeframe: str,
) -> Dataset:
    """Create a Dataset from raw bar mappings."""
    if not bars:
        raise ValueError("bars sequence must not be empty")

    normalized = []
    for bar in bars:
        normalized.append({key: _normalize_bar_value(key, value) for key, value in bar.items()})

    sorted_bars = sorted(normalized, key=lambda item: item["timestamp"])
    ta_bars = [
        Bar.from_raw(
            ts=item["timestamp"],
            open=item["open"],
            high=item["high"],
            low=item["low"],
            close=item["close"],
            volume=item.get("volume", 0.0),
            is_closed=item.get("is_closed", True),
        )
        for item in sorted_bars
    ]

    ohlcv = OHLCV.from_bars(ta_bars, symbol=str(symbol), timeframe=str(timeframe))
    dataset_obj = Dataset()
    dataset_obj.add_series(symbol=str(symbol), timeframe=str(timeframe), series=ohlcv)
    return dataset_obj


def trim_dataset(dataset_obj: Dataset, *, symbol: str, timeframe: str, trim: int) -> Dataset:
    """Trim a dataset to account for indicator lookback requirements."""
    if trim <= 0:
        return dataset_obj

    series = dataset_obj.series(symbol, timeframe)
    if series is None:
        raise ValueError(f"Dataset missing series for {symbol} {timeframe}")

    try:
        trimmed = series[trim:]
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("Failed to trim dataset for indicator lookback") from exc

    if len(trimmed) == 0:
        raise ValueError("Not enough historical bars remain after applying lookback trim")

    dataset_obj.add_series(symbol=symbol, timeframe=timeframe, series=trimmed)
    return dataset_obj
