"""Indicator catalog utilities for describing, coercing, and serializing indicators."""

from .catalog import CatalogBuilder, describe_indicator, list_catalog, list_catalog_metadata
from .params import ParameterParser, coerce_parameter, coerce_parameters
from .rust_catalog import get_rust_indicator_meta, list_rust_catalog, rust_catalog_available
from .serializer import OutputSerializer, serialize_series
from .type_parser import TypeParser, classify_parameter_type
from .utils import jsonify_value, to_epoch_seconds, to_float

__all__ = [
    # Catalog builders
    "CatalogBuilder",
    "list_catalog",
    "describe_indicator",
    "list_catalog_metadata",
    "rust_catalog_available",
    "list_rust_catalog",
    "get_rust_indicator_meta",
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
