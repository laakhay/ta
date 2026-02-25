from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel
from .rolling import RollingMaxKernel, RollingMinKernel


@dataclass(frozen=True)
class StochasticState:
    k_period: int
    high_max_state: Any
    low_min_state: Any


class StochasticKernel(Kernel[StochasticState]):
    def initialize(self, history: list[Decimal], k_period: int = 14, **kwargs: Any) -> StochasticState:
        # History here is assumed to be 'close' if called as an indicator,
        # but Stochastic needs high/low too.
        # For now, we initialize with empty rolling states.
        max_kernel = RollingMaxKernel()
        min_kernel = RollingMinKernel()

        # We don't have high/low history here easily in this abstraction layer
        # unless we pass it specifically. For incremental streaming from scratch, [] is fine.
        h_state = max_kernel.initialize([], k_period)
        l_state = min_kernel.initialize([], k_period)

        return StochasticState(k_period=k_period, high_max_state=h_state, low_min_state=l_state)

    def step(self, state: StochasticState, x_t: Decimal, **kwargs: Any) -> tuple[StochasticState, Decimal]:
        # x_t here is expected to be a tuple (high, low, close) passed by coerce_incremental_input
        if not isinstance(x_t, tuple) or len(x_t) < 3:
            # Fallback if coercion didn't happen (should not happen if registry is correct)
            return state, Decimal("NaN")

        high, low, close = x_t

        max_kernel = RollingMaxKernel()
        min_kernel = RollingMinKernel()

        new_h_state, h_high = max_kernel.step(state.high_max_state, high, state.k_period)
        new_l_state, l_low = min_kernel.step(state.low_min_state, low, state.k_period)

        # %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
        denom = h_high - l_low
        if denom == 0:
            k = Decimal("50")
        else:
            k = Decimal("100") * (close - l_low) / denom

        # Check if we are still warming up (RollingMax returns 0 if not enough data? No, it returns current max)
        # But Indicators use availability_mask. Kernels return NaN for warmup if they want.
        # Actually, let's check window size in states.
        # If window size < k_period, it's warmup.
        if len(new_h_state.window) < state.k_period:
            return StochasticState(state.k_period, new_h_state, new_l_state), Decimal("NaN")

        return StochasticState(state.k_period, new_h_state, new_l_state), k
