from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import TypeVar

from ..models import Candle

T = TypeVar("T", float, int)


def slice_tail(seq: list[T] | tuple[T, ...], n: int) -> list[T] | tuple[T, ...]:
    """Return the last n elements without copying (when possible)."""
    if n <= 0:
        return seq[:0]
    if n >= len(seq):
        return seq
    return seq[-n:]


def last_closed_ts(candles: list[Candle]) -> datetime | None:
    """Return timestamp of the last closed candle in the sequence (if any)."""
    for c in reversed(candles):
        if c.is_closed:
            return c.timestamp
    return None


def ensure_only_closed(candles: list[Candle]) -> list[Candle]:
    """Filter out any trailing open candle; return original sequence if last is closed."""
    if not candles:
        return candles
    if candles[-1].is_closed:
        return candles
    return candles[:-1]


def zscore(values: list[float | int]) -> tuple[float, float]:
    """
    Return (mu, sigma) for simple z-scoring; callers can compute z = (x-mu)/sigma.
    """
    if not values:
        return (0.0, 0.0)
    mu = mean(values)
    # Simple, robust std; avoid heavy deps here
    var = mean([(v - mu) ** 2 for v in values])
    sigma = var**0.5
    return (float(mu), float(sigma))
