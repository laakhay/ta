"""Numeric coercion helpers."""

from decimal import Decimal
from typing import Any

from .types import Price, PriceLike, Qty, QtyLike, Rate, RateLike


def coerce_price(value: PriceLike | Any) -> Price:
    if not isinstance(value, (PriceLike)):
        raise TypeError(f"Invalid price value: {value}")
    return Decimal(str(value))


def coerce_qty(value: QtyLike | Any) -> Qty:
    if not isinstance(value, (QtyLike)):
        raise TypeError(f"Invalid quantity value: {value}")
    return Decimal(str(value))


def coerce_rate(value: RateLike | Any) -> Rate:
    if not isinstance(value, (RateLike)):
        raise TypeError(f"Invalid rate value: {value}")
    return Decimal(str(value))
