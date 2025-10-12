"""TA Core module exports."""

from .base import BaseIndicator
from .io import TAInput, TAOutput
from .registry import get_indicator, list_indicators, register
from .spec import (
    DataKind,
    IndicatorRef,
    IndicatorRequirements,
    PriceField,
    RawDataRequirement,
    WindowSpec,
)

__all__ = [
    # Base
    "BaseIndicator",
    # I/O
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
