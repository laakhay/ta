from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Tuple


@dataclass
class VortexVMState:
    prev_high: Decimal | None
    prev_low: Decimal | None


class VortexVMKernel:
    """Kernel to calculate Vortex VM+ and VM- components.

    Returns (vm_plus, vm_minus) for each bar.
    """

    def initialize(self, xs: list[Any], **params: Any) -> VortexVMState:
        return VortexVMState(prev_high=None, prev_low=None)

    def step(
        self, state: VortexVMState, x: Tuple[Decimal, Decimal], **params: Any
    ) -> Tuple[VortexVMState, Tuple[Decimal, Decimal]]:
        high, low = x

        if state.prev_high is None:
            return VortexVMState(prev_high=high, prev_low=low), (Decimal(0), Decimal(0))

        vm_plus = abs(high - state.prev_low)
        vm_minus = abs(low - state.prev_high)

        return VortexVMState(prev_high=high, prev_low=low), (vm_plus, vm_minus)
