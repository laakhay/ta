"""Laakhay TA - Professional Technical Analysis Library.

A stateless, data-source agnostic technical analysis engine for cryptocurrencies.

Usage:
    >>> from laakhay.ta.models import Candle
    >>> from laakhay.ta.core import BaseIndicator

    # Any data source that provides Candle objects can use laakhay-ta
"""

__version__ = "0.1.0"

# Export models for data source integrations
# Import indicators to register them (must come after imports to avoid circular deps)
from . import indicators  # noqa: F401

# Export core contracts
from .core.base import BaseIndicator
from .core.io import TAInput, TAOutput
from .core.registry import get_indicator, list_indicators, register
from .core.spec import (
    DataKind,
    IndicatorRef,
    IndicatorRequirements,
    PriceField,
    RawDataRequirement,
    WindowSpec,
)
from .models import Candle, FundingRate, MarkPrice, OpenInterest

__all__ = [
    # Version
    "__version__",
    # Models - for data providers
    "Candle",
    "FundingRate",
    "MarkPrice",
    "OpenInterest",
    # Core contracts - for indicator developers
    "BaseIndicator",
    "TAInput",
    "TAOutput",
    # Registry
    "register",
    "get_indicator",
    "list_indicators",
    # Specs
    "DataKind",
    "PriceField",
    "WindowSpec",
    "RawDataRequirement",
    "IndicatorRef",
    "IndicatorRequirements",
]
