"""Trend indicators.

This module contains trend-following indicators that help identify
market direction and trend strength.
"""

from .sma import sma
from .ema import ema
from .macd import macd
from .bbands import bbands

__all__ = [
    "sma",
    "ema",
    "macd", 
    "bbands",
]
