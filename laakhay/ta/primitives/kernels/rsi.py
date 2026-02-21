"""RSI Kernel implementation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


@dataclass
class RSIState:
    """State for RSI."""

    period: int
    prev_close: Decimal | None
    avg_gain: Decimal | None
    avg_loss: Decimal | None


class RSIKernel(Kernel[RSIState]):
    """Kernel for evaluating Relative Strength Index."""

    def initialize(self, history: list[Decimal], **params: Any) -> RSIState:
        period = int(params.get("period", 14))

        if not history:
            return RSIState(period=period, prev_close=None, avg_gain=None, avg_loss=None)

        if len(history) < 2:
            return RSIState(period=period, prev_close=history[-1], avg_gain=None, avg_loss=None)

        gains = []
        losses = []
        for i in range(1, len(history)):
            diff = history[i] - history[i - 1]
            gains.append(diff if diff > 0 else Decimal(0))
            losses.append(-diff if diff < 0 else Decimal(0))

        n = min(len(gains), period)
        if n == 0:
            return RSIState(period=period, prev_close=history[-1], avg_gain=None, avg_loss=None)

        first_avg_gain = sum(gains[:n]) / Decimal(n)
        first_avg_loss = sum(losses[:n]) / Decimal(n)

        curr_gain = first_avg_gain
        curr_loss = first_avg_loss

        for i in range(n, len(gains)):
            curr_gain = (curr_gain * Decimal(period - 1) + gains[i]) / Decimal(period)
            curr_loss = (curr_loss * Decimal(period - 1) + losses[i]) / Decimal(period)

        return RSIState(period=period, prev_close=history[-1], avg_gain=curr_gain, avg_loss=curr_loss)

    def step(self, state: RSIState, x_t: Decimal, **params: Any) -> tuple[RSIState, Decimal]:
        if state.prev_close is None:
            state.prev_close = x_t
            return state, Decimal("NaN")

        diff = x_t - state.prev_close
        gain = diff if diff > 0 else Decimal(0)
        loss = -diff if diff < 0 else Decimal(0)

        if state.avg_gain is None or state.avg_loss is None:
            new_state = RSIState(period=state.period, prev_close=x_t, avg_gain=gain, avg_loss=loss)
            return new_state, Decimal("NaN")

        new_avg_gain = (state.avg_gain * Decimal(state.period - 1) + gain) / Decimal(state.period)
        new_avg_loss = (state.avg_loss * Decimal(state.period - 1) + loss) / Decimal(state.period)
        new_state = RSIState(period=state.period, prev_close=x_t, avg_gain=new_avg_gain, avg_loss=new_avg_loss)

        if new_avg_loss == Decimal(0):
            rsi = Decimal(100) if new_avg_gain > 0 else Decimal(50)
        else:
            rs = new_avg_gain / new_avg_loss
            rsi = Decimal(100) - (Decimal(100) / (Decimal(1) + rs))

        rsi = max(Decimal(0), min(Decimal(100), rsi))
        return new_state, rsi
