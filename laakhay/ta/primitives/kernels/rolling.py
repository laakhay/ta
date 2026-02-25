from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


@dataclass(frozen=True)
class RollingState:
    window: tuple[Decimal, ...]
    sum_x: Decimal


class RollingSumKernel(Kernel[RollingState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> RollingState:
        win = tuple(history[-period:]) if history else ()
        return RollingState(window=win, sum_x=sum(win) if win else Decimal(0))

    def step(self, state: RollingState, x_t: Decimal, period: int, **kwargs: Any) -> tuple[RollingState, Decimal]:
        new_win = list(state.window)
        new_win.append(x_t)
        if len(new_win) > period:
            dropped = new_win.pop(0)
        else:
            dropped = Decimal(0)

        new_sum = state.sum_x + x_t - dropped
        return RollingState(window=tuple(new_win), sum_x=new_sum), new_sum


class RollingMeanKernel(Kernel[RollingState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> RollingState:
        win = tuple(history[-period:]) if history else ()
        return RollingState(window=win, sum_x=sum(win) if win else Decimal(0))

    def step(self, state: RollingState, x_t: Decimal, period: int, **kwargs: Any) -> tuple[RollingState, Decimal]:
        new_win = list(state.window)
        new_win.append(x_t)
        if len(new_win) > period:
            dropped = new_win.pop(0)
        else:
            dropped = Decimal(0)

        new_sum = state.sum_x + x_t - dropped
        mean = new_sum / Decimal(period) if len(new_win) == period else Decimal(0)
        return RollingState(window=tuple(new_win), sum_x=new_sum), mean


@dataclass(frozen=True)
class RollingStdState:
    window: tuple[Decimal, ...]
    sum_x: Decimal
    sum_x2: Decimal


class RollingStdKernel(Kernel[RollingStdState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> RollingStdState:
        win = tuple(history[-period:]) if history else ()
        s1 = sum(win) if win else Decimal(0)
        s2 = sum(x * x for x in win) if win else Decimal(0)
        return RollingStdState(window=win, sum_x=s1, sum_x2=s2)

    def step(
        self,
        state: RollingStdState,
        x_t: Decimal,
        period: int,
        **kwargs: Any,
    ) -> tuple[RollingStdState, Decimal]:
        new_win = list(state.window)
        new_win.append(x_t)
        if len(new_win) > period:
            dropped = new_win.pop(0)
        else:
            dropped = Decimal(0)

        new_s1 = state.sum_x + x_t - dropped
        new_s2 = state.sum_x2 + (x_t * x_t) - (dropped * dropped)

        var = Decimal(0)
        if len(new_win) >= period:
            mean = new_s1 / Decimal(period)
            var = (new_s2 / Decimal(period)) - (mean * mean)
            if var < 0:
                var = Decimal(0)

        std = var.sqrt() if var > 0 else Decimal(0)
        return RollingStdState(window=tuple(new_win), sum_x=new_s1, sum_x2=new_s2), std


@dataclass(frozen=True)
class _MonotonicWindowState:
    window: tuple[tuple[int, Decimal], ...]
    mono: tuple[tuple[int, Decimal], ...]
    next_idx: int


def _init_monotonic_state(history: list[Decimal], *, is_max: bool) -> _MonotonicWindowState:
    window_q: deque[tuple[int, Decimal]] = deque()
    mono_q: deque[tuple[int, Decimal]] = deque()
    idx = 0
    for x in history:
        entry = (idx, x)
        window_q.append(entry)
        if is_max:
            while mono_q and mono_q[-1][1] <= x:
                mono_q.pop()
        else:
            while mono_q and mono_q[-1][1] >= x:
                mono_q.pop()
        mono_q.append(entry)
        idx += 1
    return _MonotonicWindowState(window=tuple(window_q), mono=tuple(mono_q), next_idx=idx)


def _step_monotonic(
    state: _MonotonicWindowState,
    x_t: Decimal,
    period: int,
    *,
    is_max: bool,
) -> _MonotonicWindowState:
    window_q: deque[tuple[int, Decimal]] = deque(state.window)
    mono_q: deque[tuple[int, Decimal]] = deque(state.mono)
    entry = (state.next_idx, x_t)
    window_q.append(entry)

    if is_max:
        while mono_q and mono_q[-1][1] <= x_t:
            mono_q.pop()
    else:
        while mono_q and mono_q[-1][1] >= x_t:
            mono_q.pop()
    mono_q.append(entry)

    if len(window_q) > period:
        dropped = window_q.popleft()
        if mono_q and mono_q[0][0] == dropped[0]:
            mono_q.popleft()

    return _MonotonicWindowState(window=tuple(window_q), mono=tuple(mono_q), next_idx=state.next_idx + 1)


class RollingMaxKernel(Kernel[_MonotonicWindowState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> _MonotonicWindowState:
        return _init_monotonic_state(history[-(period - 1) :] if period > 1 else history, is_max=True)

    def step(
        self,
        state: _MonotonicWindowState,
        x_t: Decimal,
        period: int,
        **kwargs: Any,
    ) -> tuple[_MonotonicWindowState, Decimal]:
        next_state = _step_monotonic(state, x_t, period, is_max=True)
        return next_state, next_state.mono[0][1]


class RollingMinKernel(Kernel[_MonotonicWindowState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> _MonotonicWindowState:
        return _init_monotonic_state(history[-(period - 1) :] if period > 1 else history, is_max=False)

    def step(
        self,
        state: _MonotonicWindowState,
        x_t: Decimal,
        period: int,
        **kwargs: Any,
    ) -> tuple[_MonotonicWindowState, Decimal]:
        next_state = _step_monotonic(state, x_t, period, is_max=False)
        return next_state, next_state.mono[0][1]


class RollingArgmaxKernel(Kernel[_MonotonicWindowState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> _MonotonicWindowState:
        return _init_monotonic_state(history[-(period - 1) :] if period > 1 else history, is_max=True)

    def step(
        self,
        state: _MonotonicWindowState,
        x_t: Decimal,
        period: int,
        **kwargs: Any,
    ) -> tuple[_MonotonicWindowState, Decimal]:
        next_state = _step_monotonic(state, x_t, period, is_max=True)
        current_idx = next_state.window[-1][0]
        arg_idx = next_state.mono[0][0]
        return next_state, Decimal(current_idx - arg_idx)


class RollingArgminKernel(Kernel[_MonotonicWindowState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> _MonotonicWindowState:
        return _init_monotonic_state(history[-(period - 1) :] if period > 1 else history, is_max=False)

    def step(
        self,
        state: _MonotonicWindowState,
        x_t: Decimal,
        period: int,
        **kwargs: Any,
    ) -> tuple[_MonotonicWindowState, Decimal]:
        next_state = _step_monotonic(state, x_t, period, is_max=False)
        current_idx = next_state.window[-1][0]
        arg_idx = next_state.mono[0][0]
        return next_state, Decimal(current_idx - arg_idx)


@dataclass(frozen=True)
class RollingMedianState:
    window: tuple[Decimal, ...]


class RollingMedianKernel(Kernel[RollingMedianState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> RollingMedianState:
        win = tuple(history[-(period - 1) :] if period > 1 else history)
        return RollingMedianState(window=win)

    def step(
        self,
        state: RollingMedianState,
        x_t: Decimal,
        period: int,
        **kwargs: Any,
    ) -> tuple[RollingMedianState, Decimal]:
        new_win = list(state.window)
        new_win.append(x_t)
        if len(new_win) > period:
            new_win.pop(0)
        sorted_window = sorted(new_win)
        med = sorted_window[len(sorted_window) // 2]
        return RollingMedianState(window=tuple(new_win)), med


@dataclass(frozen=True)
class WMAState:
    window: tuple[Decimal, ...]


class WMAKernel(Kernel[WMAState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> WMAState:
        win = tuple(history[-(period - 1) :] if period > 1 else history)
        return WMAState(window=win)

    def step(
        self,
        state: WMAState,
        x_t: Decimal,
        period: int,
        **kwargs: Any,
    ) -> tuple[WMAState, Decimal]:
        new_win = list(state.window)
        new_win.append(x_t)
        if len(new_win) > period:
            new_win.pop(0)

        # WMA = sum(price_i * weight_i) / sum(weights)
        # weights = 1, 2, ..., period
        # sum(weights) = period * (period + 1) / 2

        wma = Decimal(0)
        if len(new_win) == period:
            weight_sum = period * (period + 1) // 2
            total = Decimal(0)
            for i, val in enumerate(new_win):
                total += val * (i + 1)
            wma = total / Decimal(weight_sum)

        return WMAState(window=tuple(new_win)), wma


__all__ = [
    "RollingArgmaxKernel",
    "RollingArgminKernel",
    "RollingMaxKernel",
    "RollingMeanKernel",
    "RollingMedianKernel",
    "RollingMedianState",
    "RollingMinKernel",
    "RollingState",
    "RollingStdKernel",
    "RollingStdState",
    "RollingSumKernel",
    "WMAKernel",
    "WMAState",
]
