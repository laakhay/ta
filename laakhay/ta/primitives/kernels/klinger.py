from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Tuple


@dataclass
class KlingerVFState:
    prev_tp: Decimal | None
    prev_trend: int
    prev_cm: Decimal


class KlingerVFKernel:
    """Kernel for Klinger Volume Force (VF)."""

    def initialize(self, xs: list[Any], **params: Any) -> KlingerVFState:
        return KlingerVFState(prev_tp=None, prev_trend=0, prev_cm=Decimal(0))

    def step(
        self, state: KlingerVFState, x: Tuple[Decimal, Decimal, Decimal, Decimal], **params: Any
    ) -> Tuple[KlingerVFState, Decimal]:
        high, low, close, volume = x
        tp = (high + low + close) / Decimal("3")
        dm = high - low

        if state.prev_tp is None:
            # First bar
            return KlingerVFState(prev_tp=tp, prev_trend=0, prev_cm=Decimal(0)), Decimal(0)

        trend = 1 if tp > state.prev_tp else -1

        # cm = prev_cm + dm if current_trend == prev_trend else prev_dm + dm
        # Actually simplified Klinger Volume Force:
        # If dm is 0, we might have issues, so safe dm
        safe_dm = dm if dm > 0 else Decimal("0.0000000001")

        # vf = volume * abs(2 * ((tp - prev_tp)/dm) - 1) * trend * 100
        vf = (
            volume
            * abs(Decimal("2") * ((tp - state.prev_tp) / safe_dm) - Decimal("1"))
            * Decimal(str(trend))
            * Decimal("100")
        )

        return KlingerVFState(prev_tp=tp, prev_trend=trend, prev_cm=Decimal(0)), vf
