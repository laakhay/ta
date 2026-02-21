import math
from typing import Any

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.series import Series


def assert_series_parity(s1: Series[Any], s2: Series[Any], tolerance: float = 1e-9) -> None:
    """Assert two series are identical in metadata, timestamps, and values."""
    assert s1.symbol == s2.symbol, f"Symbol mismatch: {s1.symbol} != {s2.symbol}"
    assert s1.timeframe == s2.timeframe, f"Timeframe mismatch: {s1.timeframe} != {s2.timeframe}"
    if len(s1.timestamps) != len(s2.timestamps):
        # BatchBackend sometimes drops leading None warmup values.
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
        if v1 is None and v2 is None:
            continue
        if v1 is None or v2 is None:
            raise AssertionError(f"Value mismatch at index {i}: {v1} != {v2}")

        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            if math.isnan(v1) and math.isnan(v2):
                continue
            assert abs(float(v1) - float(v2)) <= tolerance, (
                f"Float mismatch at index {i}: {v1} != {v2} (tolerance: {tolerance})"
            )
        else:
            assert v1 == v2, f"Value mismatch at index {i}: {v1} != {v2}"


def assert_dict_parity(
    d1: dict[tuple[str, str, str], Series[Any]], d2: dict[tuple[str, str, str], Series[Any]], tolerance: float = 1e-9
) -> None:
    """Assert two dictionary outputs are identical."""
    assert set(d1.keys()) == set(d2.keys()), f"Key mismatch in dicts: {d1.keys()} != {d2.keys()}"

    for key in d1.keys():
        try:
            assert_series_parity(d1[key], d2[key], tolerance)
        except AssertionError as e:
            raise AssertionError(f"Mismatch at key {key}: {str(e)}") from e


def assert_dataset_parity(ds1: Dataset, ds2: Dataset, tolerance: float = 1e-9) -> None:
    """Assert two dataset outputs are identical."""
    assert set(ds1.keys) == set(ds2.keys), f"Dataset keys mismatch: {ds1.keys} != {ds2.keys}"
    for key in ds1.keys:
        series1 = ds1.get(key.symbol, key.timeframe, key.source)
        series2 = ds2.get(key.symbol, key.timeframe, key.source)
        if hasattr(series1, "to_series"):
            for field in ["open", "high", "low", "close", "volume"]:
                # Basic check for OHLCV
                assert_series_parity(series1.to_series(field), series2.to_series(field), tolerance)
        else:
            assert_series_parity(series1, series2, tolerance)
