"""ATR Kernel implementation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


@dataclass
class ATRState:
    """State for ATR."""

    period: int
    prev_close: Decimal | None
    rma_tr: Decimal | None
    count: int = 0


class ATRKernel(Kernel[ATRState]):
    """Kernel for evaluating Average True Range (ATR)."""

    def initialize(self, history: list[Decimal], **params: Any) -> ATRState:
        period = int(params.get("period", 14))

        if not history:
            return ATRState(period=period, prev_close=None, rma_tr=None)

        if len(history) < 1:
            return ATRState(period=period, prev_close=None, rma_tr=None, count=len(history))

        n = min(len(history), period)
        if n == 0:
            return ATRState(period=period, prev_close=None, rma_tr=None, count=len(history))

        curr_rma = sum(history[:n]) / Decimal(n)
        for i in range(n, len(history)):
            curr_rma = (curr_rma * Decimal(period - 1) + history[i]) / Decimal(period)

        return ATRState(period=period, prev_close=None, rma_tr=curr_rma, count=len(history))

    def step(self, state: ATRState, x_t: Decimal, **params: Any) -> tuple[ATRState, Decimal]:
        tr = x_t
        count = state.count + 1
        if state.rma_tr is None:
            new_state = ATRState(period=state.period, prev_close=state.prev_close, rma_tr=tr, count=count)
            # Batch parity: min_periods = period
            if count < state.period:
                return new_state, Decimal("NaN")
            return new_state, tr

        new_rma_tr = (state.rma_tr * Decimal(state.period - 1) + tr) / Decimal(state.period)
        new_state = ATRState(period=state.period, prev_close=state.prev_close, rma_tr=new_rma_tr, count=count)

        # Batch parity: min_periods = period
        if count < state.period:
            return new_state, Decimal("NaN")

        return new_state, new_rma_tr
