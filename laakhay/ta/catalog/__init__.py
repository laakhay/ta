"""Indicator catalog utilities for describing, coercing, and serializing indicators."""

from .catalog import CatalogBuilder, describe_indicator, list_catalog
from .params import ParameterParser, coerce_parameter, coerce_parameters
from .serializer import OutputSerializer, serialize_series
from .type_parser import TypeParser, classify_parameter_type
from .utils import jsonify_value, to_epoch_seconds, to_float

__all__ = [
    # Catalog builders
    "CatalogBuilder",
    "list_catalog",
    "describe_indicator",
    # Type parsing
    "TypeParser",
    "classify_parameter_type",
    # Parameter coercion
    "ParameterParser",
    "coerce_parameter",
    "coerce_parameters",
    # Output serialization
    "OutputSerializer",
    "serialize_series",
    # Utilities
    "jsonify_value",
    "to_epoch_seconds",
    "to_float",
]
