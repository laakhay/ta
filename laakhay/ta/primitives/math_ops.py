from __future__ import annotations

from collections.abc import Callable, Iterable
from decimal import Decimal, InvalidOperation
from typing import Any

from ..core import Series
from ..core.types import Price

DecimalOp1 = Callable[[Decimal], Decimal]
DecimalOp2 = Callable[[Decimal, Decimal], Decimal]


def _dec(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, Price):
        return Decimal(str(x))
    if isinstance(x, int | float | str):
        try:
            return Decimal(str(x))
        except InvalidOperation as e:
            raise TypeError(f"Bad numeric literal {x!r}") from e
    raise TypeError(f"Unsupported type {type(x)}")


def _empty_like(src: Series[Price]) -> Series[Price]:
    return Series[Price](timestamps=(), values=(), symbol=src.symbol, timeframe=src.timeframe)


def _build_like(src: Series[Price], stamps: Iterable[Any], vals: Iterable[Decimal]) -> Series[Price]:
    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(Price(v) for v in vals),
        symbol=src.symbol,
        timeframe=src.timeframe,
    )


def _align2(a: Series[Price], b: Series[Price]) -> None:
    if a.symbol != b.symbol or a.timeframe != b.timeframe:
        raise ValueError("mismatched metadata (symbol/timeframe)")
    if len(a) != len(b) or a.timestamps != b.timestamps:
        raise ValueError("timestamp alignment mismatch")


def ew_unary(src: Series[Price], op: DecimalOp1) -> Series[Price]:
    vals = (op(_dec(v)) for v in src.values)
    return _build_like(src, src.timestamps, vals)


def ew_binary(a: Series[Price], b: Series[Price], op: DecimalOp2) -> Series[Price]:
    _align2(a, b)
    vals = (op(_dec(x), _dec(y)) for x, y in zip(a.values, b.values, strict=True))
    return _build_like(a, a.timestamps, vals)


def ew_scalar_right(a: Series[Price], scalar: Any, op: DecimalOp2) -> Series[Price]:
    s = _dec(scalar)
    vals = (op(_dec(x), s) for x in a.values)
    return _build_like(a, a.timestamps, vals)


def ew_scalar_left(scalar: Any, b: Series[Price], op: DecimalOp2) -> Series[Price]:
    s = _dec(scalar)
    vals = (op(s, _dec(y)) for y in b.values)
    return _build_like(b, b.timestamps, vals)


__all__ = [
    "_build_like",
    "_dec",
    "_empty_like",
    "ew_binary",
    "ew_scalar_left",
    "ew_scalar_right",
    "ew_unary",
]
