"""
Central indicator registry and imports.

This module provides a clean import interface for all indicators and primitives,
eliminating circular import issues and providing a single source of truth for dependencies.
"""

# Import core dependencies once
from ..core import Series
from ..core.types import Price, Qty
from ..registry.models import SeriesContext
from ..registry.registry import register
from ..expressions.models import Literal
from ..expressions.operators import Expression

# Import primitives directly from the module to avoid circular imports
from ..primitives import (
    diff, rolling_max, rolling_mean, rolling_min, rolling_sum, rolling_std, shift,
    rolling_argmax, rolling_argmin, select,
    cumulative_sum, positive_values, negative_values,
    rolling_ema, true_range, typical_price, sign
)

# Import all indicators
from .trend.sma import sma
from .trend.ema import ema
from .trend.macd import macd
from .trend.bbands import bbands
from .momentum.rsi import rsi
from .momentum.stochastic import stochastic
from .volatility.atr import atr
from .volume.obv import obv
from .volume.vwap import vwap
from .pattern.swing import swing_points, swing_highs, swing_lows
from .pattern.fib import fib_retracement

__all__ = [
    # Core types
    "Series", "Price", "Qty", "SeriesContext", "register", "Expression", "Literal",
    # Primitives
    "diff", "rolling_max", "rolling_mean", "rolling_min", "rolling_sum", 
    "rolling_std", "shift", "rolling_argmax", "rolling_argmin", "select",
    "cumulative_sum", "positive_values", "negative_values",
    "rolling_ema", "true_range", "typical_price", "sign",
    # Indicators
    "sma", "ema", "macd", "bbands", "rsi", "stochastic", "atr", "obv", "vwap",
    "swing_points", "swing_highs", "swing_lows", "fib_retracement"
]
