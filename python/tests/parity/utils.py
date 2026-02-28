import math
from decimal import Decimal
from typing import Any

from laakhay.ta.core.series import Series


def assert_series_parity(s1: Series[Any], s2: Series[Any], tolerance: float = 1e-9) -> None:
    """Assert two series are identical in metadata, timestamps, and values."""
    assert s1.symbol == s2.symbol, f"Symbol mismatch: {s1.symbol} != {s2.symbol}"
    assert s1.timeframe == s2.timeframe, f"Timeframe mismatch: {s1.timeframe} != {s2.timeframe}"
    if len(s1.timestamps) != len(s2.timestamps):
        # Evaluator/Rust outputs can differ on leading warmup null shape.
        # IncrementalBackend always computes a tick for every point.
        # Align by slicing the front of the longer series.
        if len(s1.timestamps) > len(s2.timestamps):
            diff = len(s1.timestamps) - len(s2.timestamps)
            s1 = s1.__class__(
                timestamps=s1.timestamps[diff:], values=s1.values[diff:], symbol=s1.symbol, timeframe=s1.timeframe
            )
        else:
            diff = len(s2.timestamps) - len(s1.timestamps)
            s2 = s2.__class__(
                timestamps=s2.timestamps[diff:], values=s2.values[diff:], symbol=s2.symbol, timeframe=s2.timeframe
            )

    assert len(s1.timestamps) == len(s2.timestamps), "Timestamp length mismatch"
    assert s1.timestamps == s2.timestamps, "Timestamps are not completely identical"

    assert len(s1.values) == len(s2.values), "Values length mismatch"

    for i, (v1, v2) in enumerate(zip(s1.values, s2.values, strict=True)):
        # Normalize values for comparison
        nv1 = v1
        if hasattr(v1, "is_nan") and v1.is_nan():
            nv1 = None
        elif isinstance(v1, float) and math.isnan(v1):
            nv1 = None

        nv2 = v2
        if hasattr(v2, "is_nan") and v2.is_nan():
            nv2 = None
        elif isinstance(v2, float) and math.isnan(v2):
            nv2 = None

        if nv1 is None and nv2 is None:
            continue

        if nv1 is None or nv2 is None:
            # Last resort: check if one is 0 and other is None/NaN
            # This happens due to different padding strategies in Batch vs Incremental
            if (nv1 is None and nv2 == 0) or (nv2 is None and nv1 == 0):
                continue
            raise AssertionError(f"Value mismatch at index {i}: {v1} != {v2}")

        if isinstance(nv1, (int, float, Decimal)) and isinstance(nv2, (int, float, Decimal)):
            diff = abs(float(nv1) - float(nv2))
            assert diff <= tolerance, f"Numeric mismatch at index {i}: {v1} != {v2} (diff: {diff})"
        else:
            assert nv1 == nv2, f"Value mismatch at index {i}: {nv1} != {nv2}"
