"""Timestamp parsing and normalization utilities for laakhay-ta.

Design goals:
- Accept common timestamp representations (datetime/date/int/float/Decimal/str).
- Auto-detect epoch units: seconds, milliseconds, microseconds, nanoseconds.
- Parse ISO 8601 (supports trailing 'Z' and ±HH:MM offsets).
- Always return a timezone-aware UTC datetime (naive inputs are assumed UTC).
- No hard dependencies; optional support for NumPy/Pandas if present.

Public API:
    coerce_timestamp(value: TimestampLike, *, strict: bool = False) -> Timestamp

If strict=True:
    - Disallows non-ISO "loose" strptime fallbacks (only ISO + numeric epochs).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from .types import Timestamp, TimestampLike

# Pragmatic fallbacks
_FALLBACK_STRPTIME_PATTERNS: tuple[str, ...] = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S.%f",
    "%Y-%m-%d",  # date-only → midnight
)


def _to_utc(dt: datetime) -> datetime:
    """Return a UTC-aware datetime. Naive → assume UTC; aware → convert to UTC."""
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _is_integerish(s: str) -> bool:
    """True if string is an integer with optional leading sign."""
    if s[0] in "+-":
        s = s[1:]
    return s.isdigit()


def _detect_epoch_seconds(x: int | float | Decimal) -> float:
    """Detect epoch unit by magnitude and convert to seconds (float).

    Rationale (order-of-magnitude checks; supports negatives):
        < 1e10   → seconds      (2286-11-20 in UTC boundary)
        < 1e13   → milliseconds
        < 1e16   → microseconds
        >= 1e16  → nanoseconds (or absurdly large → treat as ns)
    """
    ax = abs(int(x))
    if ax < 10_000_000_000:  # < 1e10
        return float(x)
    if ax < 10_000_000_000_000:  # < 1e13
        return float(x) / 1_000
    if ax < 10_000_000_000_000_000:  # < 1e16
        return float(x) / 1_000_000
    return float(x) / 1_000_000_000  # ns


def coerce_timestamp(value: TimestampLike | Any, *, strict: bool = False) -> Timestamp:
    """Coerce common representations into a UTC-aware datetime.

    Accepted inputs
    ---------------
    - datetime: naive → assume UTC; aware → converted to UTC
    - date:     treated as midnight UTC
    - int/float/Decimal: epoch in s/ms/µs/ns (auto-detected by magnitude)
    - str:
        * ISO 8601 (YYYY-MM-DD[THH:MM:SS[.ffffff]] [Z|±HH:MM])
        * integer-like epoch strings (s/ms/µs/ns by magnitude)
        * (if strict=False) small set of pragmatic strptime fallbacks

    Parameters
    ----------
    value : TimestampLike
        The input to normalize.
    strict : bool, default False
        If True, only accepts ISO 8601 and numeric epochs; fails on fallback formats.

    Returns
    -------
    datetime (UTC-aware)

    Raises
    ------
    ValueError
        If the value cannot be parsed into a valid timestamp.
    """

    if not isinstance(value, (TimestampLike)):
        raise TypeError(f"Invalid timestamp value: {value}")

    # Fast paths
    if isinstance(value, datetime):
        return _to_utc(value)

    if isinstance(value, date):
        # Treat date-only as midnight UTC
        return datetime(value.year, value.month, value.day, tzinfo=UTC)

    if isinstance(value, int | float | Decimal):
        secs = _detect_epoch_seconds(value)
        return datetime.fromtimestamp(secs, tz=UTC)

    # only string reaches here
    s = value.strip()
    if not s:
        raise ValueError("Invalid timestamp: empty string")

    # 1) ISO 8601 (support 'Z')
    try:
        iso = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(iso)
        return _to_utc(dt)
    except ValueError:
        pass

    # 2) Integer-like epoch string (with optional sign)
    if _is_integerish(s):
        secs = _detect_epoch_seconds(int(s))
        return datetime.fromtimestamp(secs, tz=UTC)

    # 3) Float-like epoch string (e.g., "1688495599.123" or "1.697e9")
    try:
        f = float(s)
        secs = _detect_epoch_seconds(f)
        return datetime.fromtimestamp(secs, tz=UTC)
    except Exception:
        pass

    # 4) Fallback strptime patterns (only if not strict)
    if not strict:
        for fmt in _FALLBACK_STRPTIME_PATTERNS:
            try:
                dt = datetime.strptime(s, fmt)
                return _to_utc(dt)
            except ValueError:
                continue

    raise ValueError(f"Invalid timestamp string: {value!r}")
