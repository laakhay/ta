from __future__ import annotations

from typing import Any

from ..core import Bar, Price, Qty, Rate, Series, Timestamp, dataset
from ..engine import Engine
from ..expressions import BinaryOp, Expression, ExpressionNode, Literal, UnaryOp, as_expression
from ..io.csv import from_csv, to_csv
from ..primitives import cumulative_sum as _cumulative_sum
from ..primitives import diff as _diff
from ..primitives import negative_values as _negative_values
from ..primitives import positive_values as _positive_values
from ..primitives import rolling_max as _rolling_max
from ..primitives import rolling_mean as _rolling_mean
from ..primitives import rolling_min as _rolling_min
from ..primitives import rolling_std as _rolling_std
from ..primitives import rolling_sum as _rolling_sum
from ..primitives import shift as _shift
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
from .namespace import TASeries, TANamespace, indicator, literal, ta

# Primitive convenience wrappers -----------------------------------------------------------

def rolling_mean(period: int):
    return indicator("rolling_mean", period=period)


def rolling_sum(period: int):
    return indicator("rolling_sum", period=period)


def rolling_max(period: int):
    return indicator("max", period=period)


def rolling_min(period: int):
    return indicator("min", period=period)


def rolling_std(period: int):
    return indicator("rolling_std", period=period)


def diff():
    return indicator("diff")


def shift(periods: int):
    return indicator("shift", periods=periods)


def cumulative_sum():
    return indicator("cumulative_sum")


def positive_values():
    return indicator("positive_values")


def negative_values():
    return indicator("negative_values")


def rolling_ema(period: int = 20):
    return indicator("rolling_ema", period=period)


def true_range():
    return indicator("true_range")


def typical_price():
    return indicator("typical_price")


def sign():
    return indicator("sign")


def downsample(factor: int = 2, agg: str = "last", target: str = "close"):
    return indicator("downsample", factor=factor, agg=agg, target=target)


def upsample(factor: int = 2, method: str = "ffill"):
    return indicator("upsample", factor=factor, method=method)


def sync_timeframe(reference: Series[Any] | None = None, fill: str = "ffill"):
    if reference is None:
        return indicator("sync_timeframe", fill=fill)
    return indicator("sync_timeframe", reference=reference, fill=fill)


# Trigger indicator registrations
from .. import indicators  # noqa: F401,E402


__all__ = [
    "Bar",
    "Price",
    "Qty",
    "Rate",
    "Timestamp",
    "dataset",
    "from_csv",
    "to_csv",
    "ParamSchema",
    "OutputSchema",
    "IndicatorSchema",
    "register",
    "indicator",
    "literal",
    "describe_indicator",
    "describe_all",
    "indicator_info",
    "SeriesContext",
    "list_indicators",
    "list_all_names",
    "Expression",
    "ExpressionNode",
    "BinaryOp",
    "UnaryOp",
    "Literal",
    "as_expression",
    "Engine",
    "ta",
    "IndicatorHandle",
    "TASeries",
    "TANamespace",
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
]
