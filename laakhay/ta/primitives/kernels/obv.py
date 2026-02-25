from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Tuple


@dataclass
class OBVState:
    prev_close: Decimal | None
    current_obv: Decimal


class OBVKernel:
    """Kernel for On-Balance Volume (OBV)."""

    def initialize(self, xs: list[Any], **params: Any) -> OBVState:
        # OBV usually starts with the first volume value
        if not xs:
            return OBVState(prev_close=None, current_obv=Decimal(0))

        # If we have warmup data (though OBV usually doesn't need it)
        # We'd process it here. But run_kernel with min_periods=1
        # usually passes empty xs.
        return OBVState(prev_close=None, current_obv=Decimal(0))

    def step(self, state: OBVState, x: Tuple[Decimal, Decimal], **params: Any) -> Tuple[OBVState, Decimal]:
        close, volume = x

        if state.prev_close is None:
            # First bar
            new_obv = volume
            return OBVState(prev_close=close, current_obv=new_obv), new_obv

        if close > state.prev_close:
            new_obv = state.current_obv + volume
        elif close < state.prev_close:
            new_obv = state.current_obv - volume
        else:
            new_obv = state.current_obv

        return OBVState(prev_close=close, current_obv=new_obv), new_obv
