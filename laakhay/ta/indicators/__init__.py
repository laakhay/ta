"""Indicator registry and implementation imports.

Internal module: imports here trigger registration of all indicators and primitives.
For public API use laakhay.ta (e.g., ta.sma(20), indicator("sma", period=20)).

Exports are intended for:
- Registry discovery and expression compilation
- Advanced users constructing expressions programmatically (Expression, Literal)
"""

# Import core dependencies once
# Ensure namespace-level indicators (e.g., select) are registered
from ..api.namespace import _select_indicator  # noqa: F401
from ..core import Series
from ..core.types import Price, Qty
from ..expr.algebra.operators import Expression
from ..expr.ir.nodes import LiteralNode as Literal
from ..primitives.elementwise_ops import (
    absolute_value as abs,
)
from ..primitives.elementwise_ops import (
    cumulative_sum,
    diff,
    negative_values,
    positive_values,
    shift,
    sign,
    true_range,
    typical_price,
)
from ..primitives.rolling_ops import (
    rolling_argmax,
    rolling_argmin,
    rolling_ema,
    rolling_max,
    rolling_mean,
    rolling_min,
    rolling_std,
    rolling_sum,
)
from ..primitives.select import select
from ..registry.models import SeriesContext
from ..registry.registry import register

# Import event patterns
from .events import (
    cross,
    crossdown,
    crossup,
    enter,
    exit,
    falling,
    falling_pct,
    in_channel,
    out,
    rising,
    rising_pct,
)
from .momentum.rsi import rsi
from .momentum.stochastic import stochastic
from .pattern.fib import fib_anchor_high, fib_anchor_low, fib_level_down, fib_level_up, fib_retracement
from .pattern.swing import swing_high_at, swing_highs, swing_low_at, swing_lows, swing_points
from .trend.bbands import bbands
from .trend.ema import ema
from .trend.macd import macd

# Import all indicators
from .trend.sma import sma
from .volatility.atr import atr
from .volume.obv import obv
from .volume.vwap import vwap

__all__ = [
    # Core types
    "Series",
    "Price",
    "Qty",
    "SeriesContext",
    "register",
    "Expression",
    "Literal",
    # Primitives
    "abs",
    "diff",
    "rolling_max",
    "rolling_mean",
    "rolling_min",
    "rolling_sum",
    "rolling_std",
    "shift",
    "rolling_argmax",
    "rolling_argmin",
    "select",
    "cumulative_sum",
    "positive_values",
    "negative_values",
    "rolling_ema",
    "true_range",
    "typical_price",
    "sign",
    # Indicators
    "sma",
    "ema",
    "macd",
    "bbands",
    "rsi",
    "stochastic",
    "atr",
    "obv",
    "vwap",
    "swing_points",
    "swing_highs",
    "swing_lows",
    "swing_high_at",
    "swing_low_at",
    "fib_retracement",
    "fib_anchor_high",
    "fib_anchor_low",
    "fib_level_down",
    "fib_level_up",
    # Event patterns
    "crossup",
    "crossdown",
    "cross",
    "in_channel",
    "out",
    "enter",
    "exit",
    "rising",
    "falling",
    "rising_pct",
    "falling_pct",
]
