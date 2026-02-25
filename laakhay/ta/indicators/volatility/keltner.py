"""Keltner Channels indicator implementation."""

from __future__ import annotations

from decimal import Decimal

from ...core import Series
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    SemanticsSpec,
)
from ..trend.ema import ema
from ..volatility.atr import atr

KELTNER_SPEC = IndicatorSpec(
    name="keltner",
    description="Keltner Channels",
    params={
        "ema_period": ParamSpec(name="ema_period", type=int, default=20, required=False),
        "atr_period": ParamSpec(name="atr_period", type=int, default=10, required=False),
        "multiplier": ParamSpec(name="multiplier", type=float, default=2.0, required=False),
    },
    outputs={
        "upper": OutputSpec(name="upper", type=Series, description="Upper channel line", role="line"),
        "middle": OutputSpec(name="middle", type=Series, description="Middle line (EMA)", role="line"),
        "lower": OutputSpec(name="lower", type=Series, description="Lower channel line", role="line"),
    },
    semantics=SemanticsSpec(
        required_fields=("high", "low", "close"),
        lookback_params=("ema_period", "atr_period"),
    ),
)


@register(spec=KELTNER_SPEC)
def keltner(
    ctx: SeriesContext, ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0
) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    Keltner Channels indicator.

    Middle = EMA(period)
    Upper = Middle + Multiplier * ATR(period)
    Lower = Middle - Multiplier * ATR(period)
    """
    if ema_period <= 0 or atr_period <= 0:
        raise ValueError("Keltner periods must be positive")

    middle = ema(ctx, ema_period)
    v_atr = atr(ctx, atr_period)

    # ATR is calculated over high/low/close.
    # The middle line EMA is also calculated.
    # We need to ensure they are aligned if they have different start points.
    # However, both use standard library primitives which should handle alignment.

    offset = v_atr * Decimal(str(multiplier))
    upper = middle + offset
    lower = middle - offset

    return upper, middle, lower
