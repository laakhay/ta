"""Indicator registry for managing built-in and custom indicators."""

from .models import IndicatorHandle, SeriesContext
from .registry import (
    Registry,
    describe_all,
    describe_indicator,
    get_global_registry,
    indicator,
    indicator_info,
    list_all_names,
    list_indicators,
    register,
)
from .schemas import IndicatorMetadata, IndicatorSchema, OutputSchema, ParamSchema

__all__ = [
    "IndicatorHandle",
    "SeriesContext",
    "ParamSchema",
    "OutputSchema",
    "IndicatorSchema",
    "IndicatorMetadata",
    "Registry",
    "register",
    "indicator",
    "describe_indicator",
    "describe_all",
    "indicator_info",
    "list_indicators",
    "list_all_names",
    "get_global_registry",
]
