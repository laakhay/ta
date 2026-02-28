"""Utility functions for catalog and serialization."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Any


def jsonify_value(value: Any) -> Any:
    """Convert value to JSON-serializable format.

    Handles Decimal, lists, tuples, dicts, and other common types.

    Args:
        value: Value to convert

    Returns:
        JSON-serializable value
    """
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list | tuple):
        return [jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {key: jsonify_value(val) for key, val in value.items()}
    return value


def to_epoch_seconds(ts: Any) -> int | None:
    """Convert timestamp to epoch seconds.

    Args:
        ts: Timestamp to convert (datetime, int, float, or None)

    Returns:
        Epoch seconds as int, or None if conversion fails
    """
    if isinstance(ts, datetime):
        return int(ts.timestamp())
    if isinstance(ts, int | float):
        return int(ts)
    return None


def to_float(value: Any) -> float | None:
    """Convert value to float, handling edge cases.

    Handles Decimal, bool, None, NaN, and infinity.

    Args:
        value: Value to convert

    Returns:
        Float value, or None if conversion fails or value is invalid
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        try:
            value = float(value)
        except (ValueError, OverflowError):
            return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(converted) or math.isinf(converted):
        return None
    return converted
