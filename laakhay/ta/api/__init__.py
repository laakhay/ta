from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..core import Bar, Price, Qty, Rate, Series, Timestamp
from ..core.dataset import dataset
from ..data.csv import from_csv, to_csv

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
from .namespace import (
    TANamespace,
    TASeries,
    indicator,
    literal,
    ref,
    resample,
    source,
    ta,
)

# Primitive convenience wrappers -----------------------------------------------------------


def _call_indicator(
    name: str,
    args: Iterable[Any],
    kwargs: dict[str, Any],
    param_order: tuple[str, ...] = (),
) -> Any:
    """Shared helper that supports both functional and handle-style calls.

    Examples
    --------
    >>> ta.sma(20)                  # returns handle
    >>> ta.sma(series, period=20)   # evaluates on series
    >>> ta.sma(series, 20)          # positional period
    >>> ta.sma(dataset, period=20)  # evaluates on dataset
    """

    args = list(args)
    series_or_dataset: Any | None = None
    if args and isinstance(args[0], Series):
        series_or_dataset = args.pop(0)
    elif args and hasattr(args[0], "to_context"):
        # Dataset-like object (duck typing to avoid circular import)
        series_or_dataset = args.pop(0)

    if len(args) > len(param_order):
        raise TypeError(f"Too many positional arguments for indicator '{name}'. Expected at most {len(param_order)}")

    params: dict[str, Any] = {}
    for name_key, value in zip(param_order, args, strict=False):
        if value is not None:
            params[name_key] = value
    params.update(kwargs)

    handle = indicator(name, **params)
    if series_or_dataset is not None:
        return handle(series_or_dataset)
    return handle


# Primitive convenience wrappers -----------------------------------------------------------


def rolling_mean(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_mean", args, kwargs, param_order=("period",))


def rolling_sum(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_sum", args, kwargs, param_order=("period",))


def rolling_max(*args: Any, **kwargs: Any):
    return _call_indicator("max", args, kwargs, param_order=("period",))


def rolling_min(*args: Any, **kwargs: Any):
    return _call_indicator("min", args, kwargs, param_order=("period",))


def rolling_std(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_std", args, kwargs, param_order=("period",))


def diff(*args: Any, **kwargs: Any):
    return _call_indicator("diff", args, kwargs)


def shift(*args: Any, **kwargs: Any):
    return _call_indicator("shift", args, kwargs, param_order=("periods",))


def cumulative_sum(*args: Any, **kwargs: Any):
    return _call_indicator("cumulative_sum", args, kwargs)


def positive_values(*args: Any, **kwargs: Any):
    return _call_indicator("positive_values", args, kwargs)


def negative_values(*args: Any, **kwargs: Any):
    return _call_indicator("negative_values", args, kwargs)


def rolling_ema(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_ema", args, kwargs, param_order=("period",))


def true_range(*args: Any, **kwargs: Any):
    return _call_indicator("true_range", args, kwargs)


def typical_price(*args: Any, **kwargs: Any):
    return _call_indicator("typical_price", args, kwargs)


def sign(*args: Any, **kwargs: Any):
    return _call_indicator("sign", args, kwargs)


def downsample(*args: Any, **kwargs: Any):
    return _call_indicator("downsample", args, kwargs, param_order=("factor",))


def upsample(*args: Any, **kwargs: Any):
    return _call_indicator("upsample", args, kwargs, param_order=("factor",))


def sync_timeframe(*args: Any, **kwargs: Any):
    return _call_indicator("sync_timeframe", args, kwargs)


# High-level indicator shortcuts -----------------------------------------------------------


def sma(*args: Any, **kwargs: Any):
    return _call_indicator("sma", args, kwargs, param_order=("period",))


def ema(*args: Any, **kwargs: Any):
    return _call_indicator("ema", args, kwargs, param_order=("period",))


def macd(*args: Any, **kwargs: Any):
    return _call_indicator(
        "macd",
        args,
        kwargs,
        param_order=("fast_period", "slow_period", "signal_period"),
    )


def bbands(*args: Any, **kwargs: Any):
    return _call_indicator("bbands", args, kwargs, param_order=("period", "std_dev"))


def rsi(*args: Any, **kwargs: Any):
    return _call_indicator("rsi", args, kwargs, param_order=("period",))


def stochastic(*args: Any, **kwargs: Any):
    return _call_indicator("stochastic", args, kwargs, param_order=("k_period", "d_period"))


def atr(*args: Any, **kwargs: Any):
    return _call_indicator("atr", args, kwargs, param_order=("period",))


def obv(*args: Any, **kwargs: Any):
    return _call_indicator("obv", args, kwargs)


def vwap(*args: Any, **kwargs: Any):
    return _call_indicator("vwap", args, kwargs)


# Trigger indicator registrations
from .. import indicators  # noqa: F401,E402


def __getattr__(name: str) -> Any:
    """Lazy import for Engine and expression types to avoid circular imports."""
    if name == "Engine":
        from ..expr.runtime.engine import Engine

        return Engine
    elif name in ("Expression", "BinaryOp", "ExpressionNode", "Literal", "UnaryOp", "as_expression"):
        from ..expr.algebra import (
            BinaryOp,
            Expression,
            ExpressionNode,
            Literal,
            UnaryOp,
            as_expression,
        )

        if name == "Expression":
            return Expression
        elif name == "BinaryOp":
            return BinaryOp
        elif name == "ExpressionNode":
            return ExpressionNode
        elif name == "Literal":
            return Literal
        elif name == "UnaryOp":
            return UnaryOp
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
    "Series",
    "from_csv",
    "to_csv",
    "ParamSchema",
    "OutputSchema",
    "IndicatorSchema",
    "register",
    "indicator",
    "literal",
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
    "ExpressionNode",
    "BinaryOp",
    "UnaryOp",
    "Literal",
    "as_expression",
    "Engine",  # Imported lazily
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
    "sma",
    "ema",
    "macd",
    "bbands",
    "rsi",
    "stochastic",
    "atr",
    "obv",
    "vwap",
]
