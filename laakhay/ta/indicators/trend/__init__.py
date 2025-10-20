"""Trend indicators.

This module contains trend-following indicators that help identify
market direction and trend strength.
"""

from .bbands import bbands
from .ema import ema
from .macd import macd
from .sma import sma

__all__ = [
    "sma",
    "ema",
    "macd",
    "bbands",
]
