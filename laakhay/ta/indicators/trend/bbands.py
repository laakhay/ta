"""Bollinger Bands indicator using primitives."""

from __future__ import annotations

from ...core import Series
from ...primitives.rolling_ops import rolling_mean, rolling_std
from ...registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .. import Price, SeriesContext, register

BBANDS_SPEC = IndicatorSpec(
    name="bbands",
    description="Bollinger Bands with upper, middle, and lower bands",
    aliases=("bb",),
    params={
        "period": ParamSpec(name="period", type=int, default=20, required=False),
        "std_dev": ParamSpec(name="std_dev", type=float, default=2.0, required=False),
    },
    outputs={
        "upper": OutputSpec(
            name="upper",
            type=Series,
            description="Upper Bollinger Band",
            role="band_upper",
            extra={"area_pair": "lower"},
        ),
        "middle": OutputSpec(
            name="middle", type=Series, description="Middle Bollinger Band (moving average)", role="band_middle"
        ),
        "lower": OutputSpec(
            name="lower",
            type=Series,
            description="Lower Bollinger Band",
            role="band_lower",
            extra={"area_pair": "upper"},
        ),
    },
    semantics=SemanticsSpec(required_fields=("close",), lookback_params=("period",)),
    runtime_binding=RuntimeBindingSpec(kernel_id="bbands"),
)


@register(spec=BBANDS_SPEC)
def bbands(
    ctx: SeriesContext, period: int = 20, std_dev: float = 2.0
) -> tuple[Series[Price], Series[Price], Series[Price]]:
    """
    Bollinger Bands indicator using primitives.

    Returns (upper_band, middle_band, lower_band) where:
    - middle_band = SMA(period)
    - upper_band = middle_band + (std_dev * standard_deviation)
    - lower_band = middle_band - (std_dev * standard_deviation)
    """
    if period <= 0 or std_dev <= 0:
        raise ValueError("Bollinger Bands period and std_dev must be positive")

    close = ctx.close
    if close is None:
        return (
            close.__class__(timestamps=(), values=(), symbol=None, timeframe=None),
            close.__class__(timestamps=(), values=(), symbol=None, timeframe=None),
            close.__class__(timestamps=(), values=(), symbol=None, timeframe=None),
        )

    if len(close) == 0:
        empty = close.__class__(timestamps=(), values=(), symbol=close.symbol, timeframe=close.timeframe)
        return empty, empty, empty

    import ta_py
    from .._utils import results_to_series

    upper, middle, lower = ta_py.bbands([float(v) for v in close.values], period, std_dev)

    upper_series = results_to_series(upper, close, value_class=Price)
    mid_series = results_to_series(middle, close, value_class=Price)
    lower_series = results_to_series(lower, close, value_class=Price)

    return upper_series, mid_series, lower_series


BB_UPPER_SPEC = IndicatorSpec(
    name="bb_upper",
    description="Upper Bollinger Band",
    params={
        "period": ParamSpec(name="period", type=int, default=20, required=False),
        "std_dev": ParamSpec(name="std_dev", type=float, default=2.0, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Upper band", role="band_upper")},
    semantics=SemanticsSpec(required_fields=("close",), lookback_params=("period",)),
    runtime_binding=RuntimeBindingSpec(kernel_id="bb_upper"),
)


@register(spec=BB_UPPER_SPEC)
def bb_upper(
    ctx: SeriesContext,
    period: int = 20,
    std_dev: float = 2.0,
) -> Series[Price]:
    """
    Convenience wrapper that returns only the upper Bollinger Band.
    """
    upper_band, _, _ = bbands(ctx, period=period, std_dev=std_dev)
    return upper_band


BB_LOWER_SPEC = IndicatorSpec(
    name="bb_lower",
    description="Lower Bollinger Band",
    params={
        "period": ParamSpec(name="period", type=int, default=20, required=False),
        "std_dev": ParamSpec(name="std_dev", type=float, default=2.0, required=False),
    },
    outputs={"result": OutputSpec(name="result", type=Series, description="Lower band", role="band_lower")},
    semantics=SemanticsSpec(required_fields=("close",), lookback_params=("period",)),
    runtime_binding=RuntimeBindingSpec(kernel_id="bb_lower"),
)


@register(spec=BB_LOWER_SPEC)
def bb_lower(
    ctx: SeriesContext,
    period: int = 20,
    std_dev: float = 2.0,
) -> Series[Price]:
    """
    Convenience wrapper that returns only the lower Bollinger Band.
    """
    _, _, lower_band = bbands(ctx, period=period, std_dev=std_dev)
    return lower_band
