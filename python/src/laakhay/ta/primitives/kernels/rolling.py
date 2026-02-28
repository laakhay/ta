from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


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


__all__ = [
    "RollingArgmaxKernel",
    "RollingArgminKernel",
    "RollingMaxKernel",
    "RollingMedianKernel",
    "RollingMedianState",
    "RollingMinKernel",
]
