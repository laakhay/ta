from __future__ import annotations

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
from . import momentum, primitives, trend, volatility, volume
from .handle import IndicatorHandle
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
    # Categories
    "trend",
    "momentum",
    "volatility",
    "volume",
    "primitives",
]
