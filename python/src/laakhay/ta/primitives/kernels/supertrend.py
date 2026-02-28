"""Supertrend Kernel implementation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


@dataclass
class SupertrendState:
    """State for Supertrend."""

    multiplier: Decimal
    period: int
    prev_close: Decimal | None
    prev_upper: Decimal | None
    prev_lower: Decimal | None
    prev_supertrend: Decimal | None
    prev_direction: int | None  # 1 for bullish, -1 for bearish


class SupertrendKernel(Kernel[SupertrendState]):
    """Kernel for evaluating Supertrend."""

    def initialize(self, history: list[Any], **params: Any) -> SupertrendState:
        multiplier = Decimal(str(params.get("multiplier", 3.0)))
        period = int(params.get("period", 10))

        if not history:
            return SupertrendState(
                multiplier=multiplier,
                period=period,
                prev_close=None,
                prev_upper=None,
                prev_lower=None,
                prev_supertrend=None,
                prev_direction=None,
            )

        state = SupertrendState(
            multiplier=multiplier,
            period=period,
            prev_close=None,
            prev_upper=None,
            prev_lower=None,
            prev_supertrend=None,
            prev_direction=None,
        )

        for x_t in history:
            state, _ = self.step(state, x_t, **params)

        return state

    def step(self, state: SupertrendState, x_t: Any, **params: Any) -> tuple[SupertrendState, tuple[Decimal, Decimal]]:
        """
        x_t: (high, low, close, atr)
        Returns: (supertrend_value, direction)
        """
        h, l, c, atr = [Decimal(str(v)) for v in x_t]

        if h.is_nan() or l.is_nan() or c.is_nan() or atr.is_nan():
            return state, (Decimal("NaN"), Decimal("NaN"))

        # Basic Bands
        hl2 = (h + l) / Decimal(2)
        basic_upper = hl2 + state.multiplier * atr
        basic_lower = hl2 - state.multiplier * atr

        # Final Bands
        if (
            state.prev_upper is None
            or basic_upper < state.prev_upper
            or (state.prev_close and state.prev_close > state.prev_upper)
        ):
            final_upper = basic_upper
        else:
            final_upper = state.prev_upper

        if (
            state.prev_lower is None
            or basic_lower > state.prev_lower
            or (state.prev_close and state.prev_close < state.prev_lower)
        ):
            final_lower = basic_lower
        else:
            final_lower = state.prev_lower

        # Supertrend and Direction
        if state.prev_supertrend is None:
            direction = 1
            supertrend = final_lower
        elif state.prev_supertrend == state.prev_upper:
            if c > final_upper:
                direction = 1
                supertrend = final_lower
            else:
                direction = -1
                supertrend = final_upper
        else:  # prev_supertrend == prev_lower
            if c < final_lower:
                direction = -1
                supertrend = final_upper
            else:
                direction = 1
                supertrend = final_lower

        new_state = SupertrendState(
            multiplier=state.multiplier,
            period=state.period,
            prev_close=c,
            prev_upper=final_upper,
            prev_lower=final_lower,
            prev_supertrend=supertrend,
            prev_direction=direction,
        )

        return new_state, (supertrend, Decimal(direction))
