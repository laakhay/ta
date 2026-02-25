from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# Trigger indicator registrations
from .. import indicators  # noqa: F401,E402
from ..core import Bar, Price, Qty, Rate, Series, Timestamp
from ..data.csv import from_csv, to_csv
from ..data.dataset import dataset, dataset_from_bars, trim_dataset
from ..expr.semantics.source_schema import (
    LIQUIDATION,
    OHLCV,
    ORDERBOOK,
    SOURCE_DEFS,
    TRADES,
)

# Expression types imported lazily to avoid circular imports
from ..registry import (
    IndicatorSchema,
    OutputSchema,
    ParamSchema,
    SeriesContext,
    describe_all,
    describe_indicator,
    indicator_info,
    list_all_names,
    list_indicators,
    register,
)
from .handle import IndicatorHandle
from .momentum import (
    adx,
    ao,
    cci,
    cmo,
    coppock,
    macd,
    mfi,
    roc,
    rsi,
    stochastic,
    vortex,
    williams_r,
)
from .namespace import (
    TANamespace,
    TASeries,
    indicator,
    liquidation,
    literal,
    ohlcv,
    orderbook,
    ref,
    resample,
    source,
    ta,
    trades,
)
from .primitives import (
    cumulative_sum,
    diff,
    downsample,
    negative_values,
    positive_values,
    rolling_ema,
    rolling_max,
    rolling_mean,
    rolling_min,
    rolling_std,
    rolling_sum,
    shift,
    sign,
    sync_timeframe,
    true_range,
    typical_price,
    upsample,
)
from .trend import (
    elder_ray,
    ema,
    fib_anchor_high,
    fib_anchor_low,
    fib_level_down,
    fib_level_up,
    fisher,
    hma,
    ichimoku,
    psar,
    sma,
    supertrend,
    swing_high_at,
    swing_low_at,
    wma,
)
from .utils import _call_indicator
from .volatility import (
    atr,
    bbands,
    donchian,
    keltner,
)
from .volume import (
    cmf,
    klinger,
    obv,
    vwap,
)


def __getattr__(name: str) -> Any:
    """Lazy import for Engine and expression types to avoid circular imports."""
    if name == "Engine":
        from ..expr.execution.engine import Engine

        return Engine
    elif name in (
        "Expression",
        "as_expression",
    ):
        from ..expr.algebra import Expression, as_expression

        if name == "Expression":
            return Expression
        elif name == "as_expression":
            return as_expression
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Bar",
    "Price",
    "Qty",
    "Rate",
    "Timestamp",
    "dataset",
    "dataset_from_bars",
    "trim_dataset",
    "Series",
    "from_csv",
    "to_csv",
    "ParamSchema",
    "OutputSchema",
    "IndicatorSchema",
    "register",
    "indicator",
    "literal",
    "OHLCV",
    "TRADES",
    "ORDERBOOK",
    "LIQUIDATION",
    "SOURCE_DEFS",
    "ohlcv",
    "trades",
    "orderbook",
    "liquidation",
    "ref",
    "resample",
    "source",
    "describe_indicator",
    "describe_all",
    "indicator_info",
    "SeriesContext",
    "list_indicators",
    "list_all_names",
    "Expression",
    "as_expression",
    "Engine",  # Imported lazily
    "ta",
    "IndicatorHandle",
    "TASeries",
    "TANamespace",
    # Primitives
    "rolling_mean",
    "rolling_sum",
    "rolling_max",
    "rolling_min",
    "rolling_std",
    "diff",
    "shift",
    "cumulative_sum",
    "positive_values",
    "negative_values",
    "rolling_ema",
    "true_range",
    "typical_price",
    "sign",
    "downsample",
    "upsample",
    "sync_timeframe",
    # Trend
    "sma",
    "ema",
    "ichimoku",
    "supertrend",
    "psar",
    "hma",
    "wma",
    "elder_ray",
    "fisher",
    "swing_high_at",
    "swing_low_at",
    "fib_level_down",
    "fib_level_up",
    "fib_anchor_high",
    "fib_anchor_low",
    # Momentum
    "macd",
    "rsi",
    "stochastic",
    "adx",
    "ao",
    "cci",
    "cmo",
    "coppock",
    "mfi",
    "roc",
    "vortex",
    "williams_r",
    # Volatility
    "bbands",
    "atr",
    "donchian",
    "keltner",
    # Volume
    "obv",
    "vwap",
    "cmf",
    "klinger",
]
