"""Vortex Indicator (VI) implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.series import Series as CoreSeries
from ...core.types import Price
from ...primitives.elementwise_ops import true_range
from ...primitives.kernels.vortex import VortexVMKernel
from ...primitives.rolling_ops import rolling_sum
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)

VORTEX_SPEC = IndicatorSpec(
    name="vortex",
    description="Vortex Indicator (VI)",
    params={"period": ParamSpec(name="period", type=int, default=14, required=False)},
    outputs={
        "plus": OutputSpec(name="plus", type=Series, description="VI+", role="line"),
        "minus": OutputSpec(name="minus", type=Series, description="VI-", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("period",),
    ),
)


@register(spec=VORTEX_SPEC)
def vortex(ctx: SeriesContext, period: int = 14) -> tuple[Series[Price], Series[Price]]:
    """
    Vortex Indicator (VI).

    VI+ = Sum(abs(High - Prev Low), period) / Sum(True Range, period)
    VI- = Sum(abs(Low - Prev High), period) / Sum(True Range, period)
    """
    if period <= 0:
        raise ValueError("Vortex period must be positive")

    h, l, c = ctx.high, ctx.low, ctx.close
    n = len(c)
    if n == 0:
        empty = CoreSeries[Price](timestamps=(), values=(), symbol=c.symbol, timeframe=c.timeframe)
        return empty, empty

    # Calculate VM+ and VM- components using kernel
    hl_vals = [(Decimal(str(h.values[i])), Decimal(str(l.values[i]))) for i in range(n)]

    # We run the kernel manually to capture multi-series output efficiently
    kernel = VortexVMKernel()
    state = kernel.initialize(hl_vals[:0])

    out_vmp: list[Decimal] = []
    out_vmm: list[Decimal] = []

    for i in range(n):
        state, (vmp_val, vmm_val) = kernel.step(state, hl_vals[i])
        out_vmp.append(vmp_val)
        out_vmm.append(vmm_val)

    vm_plus_series = CoreSeries[Price](
        timestamps=c.timestamps, values=tuple(Price(v) for v in out_vmp), symbol=c.symbol, timeframe=c.timeframe
    )
    vm_minus_series = CoreSeries[Price](
        timestamps=c.timestamps, values=tuple(Price(v) for v in out_vmm), symbol=c.symbol, timeframe=c.timeframe
    )

    # Calculate True Range
    tr_series = true_range(ctx)

    # Rolling Sums
    vmp_sum = rolling_sum(SeriesContext(close=vm_plus_series), period)
    vmm_sum = rolling_sum(SeriesContext(close=vm_minus_series), period)
    tr_sum = rolling_sum(SeriesContext(close=tr_series), period)

    # Final VI lines with safe division
    vi_plus_vals = []
    vi_minus_vals = []

    for i in range(n):
        ts = Decimal(str(tr_sum.values[i]))
        if ts == 0:
            vi_plus_vals.append(Decimal(0))
            vi_minus_vals.append(Decimal(0))
        else:
            vi_plus_vals.append(Decimal(str(vmp_sum.values[i])) / ts)
            vi_minus_vals.append(Decimal(str(vmm_sum.values[i])) / ts)

    return (
        CoreSeries[Price](
            timestamps=c.timestamps,
            values=tuple(Price(v) for v in vi_plus_vals),
            symbol=c.symbol,
            timeframe=c.timeframe,
            availability_mask=vmp_sum.availability_mask,
        ),
        CoreSeries[Price](
            timestamps=c.timestamps,
            values=tuple(Price(v) for v in vi_minus_vals),
            symbol=c.symbol,
            timeframe=c.timeframe,
            availability_mask=vmm_sum.availability_mask,
        ),
    )
