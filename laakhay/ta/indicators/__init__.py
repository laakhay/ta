"""
Central indicator registry and imports.

This module provides a clean import interface for all indicators and primitives,
eliminating circular import issues and providing a single source of truth for dependencies.
"""

# Import core dependencies once
# Ensure namespace-level indicators (e.g., select) are registered
from ..api.namespace import _select_indicator  # noqa: F401
from ..core import Series
from ..core.types import Price, Qty
from ..expr.algebra.models import Literal
from ..expr.algebra.operators import Expression

# Import primitives directly from the module to avoid circular imports
from ..primitives import (
    cumulative_sum,
    diff,
    negative_values,
    positive_values,
    rolling_argmax,
    rolling_argmin,
    rolling_ema,
    rolling_max,
    rolling_mean,
    rolling_min,
    rolling_std,
    rolling_sum,
    select,
    shift,
    sign,
    true_range,
    typical_price,
)
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
from .pattern.fib import fib_retracement
from .pattern.swing import swing_highs, swing_lows, swing_points
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
    "fib_retracement",
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
