"""Data models for technical analysis.

These models define the data structures expected by indicators.
Any data source conforming to these models can be used with laakhay-ta.
"""

from .candle import Candle
from .funding_rate import FundingRate
from .mark_price import MarkPrice
from .open_interest import OpenInterest

__all__ = [
    "Candle",
    "FundingRate",
    "MarkPrice",
    "OpenInterest",
]
