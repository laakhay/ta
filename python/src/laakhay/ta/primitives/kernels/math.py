from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


@dataclass(frozen=True)
class CumulativeSumState:
    acc: Decimal


class CumulativeSumKernel(Kernel[CumulativeSumState]):
    def initialize(self, history: list[Decimal], **params: Any) -> CumulativeSumState:
        return CumulativeSumState(acc=sum(history) if history else Decimal(0))

    def step(self, state: CumulativeSumState, x_t: Decimal, **params: Any) -> tuple[CumulativeSumState, Decimal]:
        acc = state.acc + x_t
        return CumulativeSumState(acc=acc), acc


@dataclass(frozen=True)
class DiffState:
    prev: Decimal | None


class DiffKernel(Kernel[DiffState]):
    def initialize(self, history: list[Decimal], **params: Any) -> DiffState:
        return DiffState(prev=history[-1] if history else None)

    def step(self, state: DiffState, x_t: Decimal, **params: Any) -> tuple[DiffState, Decimal]:
        if state.prev is None:
            return DiffState(prev=x_t), Decimal(0)
        return DiffState(prev=x_t), x_t - state.prev


class SignKernel(Kernel[DiffState]):
    def initialize(self, history: list[Decimal], **params: Any) -> DiffState:
        return DiffState(prev=history[-1] if history else None)

    def step(self, state: DiffState, x_t: Decimal, **params: Any) -> tuple[DiffState, Decimal]:
        if state.prev is None:
            return DiffState(prev=x_t), Decimal(0)
        diff = x_t - state.prev
        if diff > 0:
            out = Decimal(1)
        elif diff < 0:
            out = Decimal(-1)
        else:
            out = Decimal(0)
        return DiffState(prev=x_t), out


@dataclass(frozen=True)
class RMAState:
    value: Decimal | None


class RMAKernel(Kernel[RMAState]):
    def initialize(self, history: list[Decimal], period: int, **params: Any) -> RMAState:
        if not history:
            return RMAState(value=None)
        alpha = Decimal(1) / Decimal(period)
        rma = history[0]
        for x in history[1:]:
            rma = alpha * x + (Decimal(1) - alpha) * rma
        return RMAState(value=rma)

    def step(self, state: RMAState, x_t: Decimal, period: int, **params: Any) -> tuple[RMAState, Decimal]:
        if state.value is None:
            return RMAState(value=x_t), x_t
        alpha = Decimal(1) / Decimal(period)
        rma = alpha * x_t + (Decimal(1) - alpha) * state.value
        return RMAState(value=rma), rma


@dataclass(frozen=True)
class StatelessState:
    pass


class AbsoluteValueKernel(Kernel[StatelessState]):
    def initialize(self, history: list[Any], **params: Any) -> StatelessState:
        return StatelessState()

    def step(self, state: StatelessState, x_t: Any, **params: Any) -> tuple[StatelessState, Decimal]:
        return state, abs(Decimal(str(x_t)))


class PositiveKernel(Kernel[StatelessState]):
    def initialize(self, history: list[Any], **params: Any) -> StatelessState:
        return StatelessState()

    def step(self, state: StatelessState, x_t: Any, **params: Any) -> tuple[StatelessState, Decimal]:
        x = Decimal(str(x_t))
        return state, x if x > 0 else Decimal(0)


class NegativeKernel(Kernel[StatelessState]):
    def initialize(self, history: list[Any], **params: Any) -> StatelessState:
        return StatelessState()

    def step(self, state: StatelessState, x_t: Any, **params: Any) -> tuple[StatelessState, Decimal]:
        x = Decimal(str(x_t))
        return state, x if x < 0 else Decimal(0)


class PairMaxKernel(Kernel[StatelessState]):
    def initialize(self, history: list[Any], **params: Any) -> StatelessState:
        return StatelessState()

    def step(self, state: StatelessState, x_t: Any, **params: Any) -> tuple[StatelessState, Decimal]:
        left, right = x_t
        return state, max(Decimal(str(left)), Decimal(str(right)))


class PairMinKernel(Kernel[StatelessState]):
    def initialize(self, history: list[Any], **params: Any) -> StatelessState:
        return StatelessState()

    def step(self, state: StatelessState, x_t: Any, **params: Any) -> tuple[StatelessState, Decimal]:
        left, right = x_t
        return state, min(Decimal(str(left)), Decimal(str(right)))


@dataclass(frozen=True)
class TrueRangeState:
    prev_close: Decimal | None


class TrueRangeKernel(Kernel[TrueRangeState]):
    def initialize(self, history: list[Any], **params: Any) -> TrueRangeState:
        prev_close: Decimal | None = None
        for x_t in history:
            high, low, close = x_t
            _ = high - low
            prev_close = close
        return TrueRangeState(prev_close=prev_close)

    def step(self, state: TrueRangeState, x_t: Any, **params: Any) -> tuple[TrueRangeState, Decimal]:
        high, low, close = x_t
        hl = high - low
        if state.prev_close is None:
            tr = hl
        else:
            hp = abs(high - state.prev_close)
            lp = abs(low - state.prev_close)
            tr = max(hl, hp, lp)
        return TrueRangeState(prev_close=close), tr


class TypicalPriceKernel(Kernel[StatelessState]):
    def initialize(self, history: list[Any], **params: Any) -> StatelessState:
        return StatelessState()

    def step(self, state: StatelessState, x_t: Any, **params: Any) -> tuple[StatelessState, Decimal]:
        high, low, close = x_t
        return state, (high + low + close) / Decimal(3)


class PassthroughKernel(Kernel[StatelessState]):
    def initialize(self, history: list[Any], **params: Any) -> StatelessState:
        return StatelessState()

    def step(self, state: StatelessState, x_t: Any, **params: Any) -> tuple[StatelessState, Decimal]:
        return state, Decimal(str(x_t))


__all__ = [
    "AbsoluteValueKernel",
    "CumulativeSumKernel",
    "CumulativeSumState",
    "DiffKernel",
    "DiffState",
    "NegativeKernel",
    "PairMaxKernel",
    "PairMinKernel",
    "PassthroughKernel",
    "PositiveKernel",
    "RMAKernel",
    "RMAState",
    "SignKernel",
    "StatelessState",
    "TrueRangeKernel",
    "TrueRangeState",
    "TypicalPriceKernel",
]
