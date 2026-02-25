"""Parabolic SAR (Stop and Reverse) kernel implementation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from ..kernel import Kernel


@dataclass(frozen=True)
class PSARState:
    af_start: Decimal
    af_increment: Decimal
    af_max: Decimal

    sar: Optional[Decimal]
    ep: Optional[Decimal]
    af: Decimal
    trend: int  # 1 for long, -1 for short

    # Historical data for floor/ceiling
    prev_high: Optional[Decimal]
    prev_prev_high: Optional[Decimal]
    prev_low: Optional[Decimal]
    prev_prev_low: Optional[Decimal]


class PSARKernel(Kernel[PSARState]):
    def initialize(self, history: list[Any], **params: Any) -> PSARState:
        af_start = Decimal(str(params.get("af_start", 0.02)))
        af_increment = Decimal(str(params.get("af_increment", 0.02)))
        af_max = Decimal(str(params.get("af_max", 0.2)))

        if not history:
            return PSARState(
                af_start=af_start,
                af_increment=af_increment,
                af_max=af_max,
                sar=None,
                ep=None,
                af=af_start,
                trend=1,
                prev_high=None,
                prev_prev_high=None,
                prev_low=None,
                prev_prev_low=None,
            )

        # Basic initialization: starting a long trend from the first bar
        h0, l0, c0 = history[0]
        h0, l0 = Decimal(str(h0)), Decimal(str(l0))

        state = PSARState(
            af_start=af_start,
            af_increment=af_increment,
            af_max=af_max,
            sar=l0,
            ep=h0,
            af=af_start,
            trend=1,
            prev_high=h0,
            prev_prev_high=None,
            prev_low=l0,
            prev_prev_low=None,
        )

        for x_t in history[1:]:
            state, _ = self.step(state, x_t, **params)

        return state

    def step(self, state: PSARState, x_t: Any, **params: Any) -> tuple[PSARState, tuple[Decimal, Decimal]]:
        """
        x_t: (high, low, close)
        Returns: (sar_value, direction)
        """
        h, l, c = [Decimal(str(v)) for v in x_t]

        if state.sar is None:
            # First bar handled by initialize or first step
            sar = l
            ep = h
            new_state = PSARState(
                af_start=state.af_start,
                af_increment=state.af_increment,
                af_max=state.af_max,
                sar=sar,
                ep=ep,
                af=state.af_start,
                trend=1,
                prev_high=h,
                prev_prev_high=None,
                prev_low=l,
                prev_prev_low=None,
            )
            return new_state, (sar, Decimal(1))

        # 1. Calculate next SAR
        sar = state.sar + state.af * (state.ep - state.sar)

        af = state.af
        ep = state.ep
        trend = state.trend

        if trend == 1:  # Long
            # Floor next SAR
            if state.prev_low is not None:
                sar = min(sar, state.prev_low)
            if state.prev_prev_low is not None:
                sar = min(sar, state.prev_prev_low)

            # Check for reversal
            if l < sar:
                trend = -1
                sar = ep
                ep = l
                af = state.af_start
            else:
                if h > ep:
                    ep = h
                    af = min(af + state.af_increment, state.af_max)
        else:  # Short
            # Ceiling next SAR
            if state.prev_high is not None:
                sar = max(sar, state.prev_high)
            if state.prev_prev_high is not None:
                sar = max(sar, state.prev_prev_high)

            # Check for reversal
            if h > sar:
                trend = 1
                sar = ep
                ep = h
                af = state.af_start
            else:
                if l < ep:
                    ep = l
                    af = min(af + state.af_increment, state.af_max)

        new_state = PSARState(
            af_start=state.af_start,
            af_increment=state.af_increment,
            af_max=state.af_max,
            sar=sar,
            ep=ep,
            af=af,
            trend=trend,
            prev_high=h,
            prev_prev_high=state.prev_high,
            prev_low=l,
            prev_prev_low=state.prev_low,
        )

        return new_state, (sar, Decimal(trend))
