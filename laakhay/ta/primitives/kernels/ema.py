from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


@dataclass(frozen=True)
class EMAState:
    last_ema: Decimal


class EMAKernel(Kernel[EMAState]):
    def initialize(self, history: list[Decimal], period: int, **kwargs: Any) -> EMAState:
        if not history:
            return EMAState(last_ema=Decimal(0))
        alpha = Decimal(2) / Decimal(period + 1)
        ema = history[0]
        for v in history[1:]:
            ema = alpha * v + (Decimal(1) - alpha) * ema
        return EMAState(last_ema=ema)

    def step(self, state: EMAState, x_t: Decimal, period: int, **kwargs: Any) -> tuple[EMAState, Decimal]:
        if state.last_ema == Decimal(0):
            ema = x_t
        else:
            alpha = Decimal(2) / Decimal(period + 1)
            ema = alpha * x_t + (Decimal(1) - alpha) * state.last_ema
        return EMAState(last_ema=ema), ema
