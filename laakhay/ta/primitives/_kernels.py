# laakhay/ta/_kernels.py
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from decimal import Decimal, InvalidOperation
from typing import Any, Tuple

from ..core import Series
from ..core.types import Price

DecimalOp1 = Callable[[Decimal], Decimal]
DecimalOp2 = Callable[[Decimal, Decimal], Decimal]
InitFn = Callable[[Iterable[Decimal]], Tuple[Any, Decimal]]
UpdateFn = Callable[[Any, Decimal, Decimal], Tuple[Any, Decimal]]
FinalizeFn = Callable[[Any], Decimal | None]


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


# -----------------------------
# Element-wise (unary/binary)
# -----------------------------


def ew_unary(src: Series[Price], op: DecimalOp1) -> Series[Price]:
    vals = (op(_dec(v)) for v in src.values)
    return _build_like(src, src.timestamps, vals)


def ew_binary(a: Series[Price], b: Series[Price], op: DecimalOp2) -> Series[Price]:
    _align2(a, b)
    vals = (op(_dec(x), _dec(y)) for x, y in zip(a.values, b.values, strict=False))
    return _build_like(a, a.timestamps, vals)


def ew_scalar_right(a: Series[Price], scalar: Any, op: DecimalOp2) -> Series[Price]:
    s = _dec(scalar)
    vals = (op(_dec(x), s) for x in a.values)
    return _build_like(a, a.timestamps, vals)


def ew_scalar_left(scalar: Any, b: Series[Price], op: DecimalOp2) -> Series[Price]:
    s = _dec(scalar)
    vals = (op(s, _dec(y)) for y in b.values)
    return _build_like(b, b.timestamps, vals)


# -----------------------------
# Rolling kernel (right-aligned)
# -----------------------------
# A single API that can:
# - run O(1) sliding updates via (init, update, finalize)
# - or fallback to a per-window evaluator
# - or use a specialized 'deque' strategy for extrema


def rolling_kernel(
    src: Series[Price],
    period: int,
    *,
    init: InitFn | None = None,
    update: UpdateFn | None = None,
    finalize: FinalizeFn | None = None,
    window_eval: Callable[[Iterable[Decimal]], Decimal] | None = None,
) -> Series[Price]:
    """Right-aligned rolling outputs. Returns empty if len < period.
    Choose one of:
      - (init, update[, finalize]) for O(n) sliding accumulators
      - window_eval for generic window function (O(n*w))
    """
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)

    xs = [_dec(v) for v in src.values]
    out: list[Decimal] = []

    if window_eval is not None:
        # Generic (O(n*w))
        for i in range(period - 1, n):
            w = xs[i - period + 1 : i + 1]
            out.append(window_eval(w))
        return _build_like(src, src.timestamps[period - 1 :], out)

    if init and update:
        # Sliding accumulator (O(n))
        state, first_val = init(xs[:period])
        out.append(first_val)
        for i in range(period, n):
            state, v = update(state, xs[i - period], xs[i])
            out.append(v)
        # Optional finalize transforms the state (rarely needed)
        # (Kept for completeness, not used in common reducers)
        return _build_like(src, src.timestamps[period - 1 :], out)

    raise ValueError("rolling_kernel: supply either (init,update) or window_eval")


# -----------------------------
# Ready-made rolling recipes
# -----------------------------


def rolling_sum_recipe(period: int):
    def _init(win: Iterable[Decimal]):
        s = sum(win)
        return s, s

    def _update(s: Decimal, out_v: Decimal, in_v: Decimal):
        s2 = s + in_v - out_v
        return s2, s2

    return _init, _update


def rolling_mean_recipe(period: int):
    init_s, upd_s = rolling_sum_recipe(period)

    def _init(win: Iterable[Decimal]):
        s, _ = init_s(win)
        m = s / Decimal(period)
        return s, m

    def _update(s: Decimal, out_v: Decimal, in_v: Decimal):
        s2, s2_val = upd_s(s, out_v, in_v)
        return s2, s2_val / Decimal(period)

    return _init, _update


def rolling_std_recipe(period: int):
    # population variance (ddof=0)
    def _init(win: Iterable[Decimal]):
        xs = list(win)
        s = sum(xs)
        ss = sum(x * x for x in xs)
        mean = s / Decimal(period)
        var = (ss / Decimal(period)) - mean * mean
        std = var.sqrt() if var >= 0 else Decimal(0)
        return (s, ss), std

    def _update(state: Tuple[Decimal, Decimal], out_v: Decimal, in_v: Decimal):
        s, ss = state
        s2 = s + in_v - out_v
        ss2 = ss + in_v * in_v - out_v * out_v
        mean = s2 / Decimal(period)
        var = (ss2 / Decimal(period)) - mean * mean
        std = var.sqrt() if var >= 0 else Decimal(0)
        return (s2, ss2), std

    return _init, _update


def rolling_max_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            out.append(xs[dq[0]])
    return _build_like(src, src.timestamps[period - 1 :], out)


def rolling_min_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] >= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            out.append(xs[dq[0]])
    return _build_like(src, src.timestamps[period - 1 :], out)


def rolling_argmax_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            offset = i - dq[0]
            out.append(Decimal(offset))
    return _build_like(src, src.timestamps[period - 1 :], out)


def rolling_argmin_deque(src: Series[Price], period: int) -> Series[Price]:
    if period <= 0:
        raise ValueError("Period must be positive")
    n = len(src)
    if n == 0 or n < period:
        return _empty_like(src)
    xs = [_dec(v) for v in src.values]
    dq: deque[int] = deque()
    out: list[Decimal] = []
    for i, v in enumerate(xs):
        while dq and xs[dq[-1]] >= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - period:
            dq.popleft()
        if i >= period - 1:
            offset = i - dq[0]
            out.append(Decimal(offset))
    return _build_like(src, src.timestamps[period - 1 :], out)
