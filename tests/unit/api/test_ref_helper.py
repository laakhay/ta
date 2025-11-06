"""Tests for the ta.ref multi-timeframe helper."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta import ta
from laakhay.ta.core import Dataset, Series
from laakhay.ta.core.types import Price


from datetime import timedelta


def _make_series(values, step: timedelta, label: str):
    timestamps = tuple(
        datetime(2024, 1, 1, tzinfo=UTC) + i * step for i in range(len(values))
    )
    return Series[Price](
        timestamps=timestamps,
        values=tuple(Decimal(str(v)) for v in values),
        symbol="BTCUSDT",
        timeframe=label,
    )


def test_ref_basic_extraction():
    dataset = Dataset()

    close_4h = _make_series([100, 110, 105], timedelta(hours=4), "4h")
    close_1h = _make_series([100, 102, 104, 106, 108, 110, 109, 108, 107], timedelta(hours=1), "1h")

    dataset.add_series("BTCUSDT", "4h", close_4h, "close")
    dataset.add_series("BTCUSDT", "1h", close_1h, "close")

    result = ta.ref(dataset, timeframe="4h", field="close", symbol="BTCUSDT")

    assert result.values == close_4h.values
    assert result.timestamps == close_4h.timestamps
    assert result.symbol == "BTCUSDT"
    assert result.timeframe == "4h"


def test_ref_with_sync_reference():
    dataset = Dataset()
    close_4h = _make_series([100, 110, 105], timedelta(hours=4), "4h")
    close_1h = _make_series(
        [100, 102, 104, 106, 108, 110, 109, 108, 107, 106, 105, 104],
        timedelta(hours=1),
        "1h",
    )

    dataset.add_series("BTCUSDT", "4h", close_4h, "close")
    dataset.add_series("BTCUSDT", "1h", close_1h, "close")

    synced = ta.ref(
        dataset,
        timeframe="4h",
        field="close",
        symbol="BTCUSDT",
        reference=("BTCUSDT", "1h", "close"),
        fill="ffill",
    )

    assert len(synced.values) == len(close_1h.values)
    assert synced.symbol == "BTCUSDT"
    # Last value should match last 4h close and propagate
    assert synced.values[-1] == close_4h.values[-1]


def test_ref_invalid_field_raises():
    dataset = Dataset()

    from datetime import timedelta

    close_4h = _make_series([100, 110, 105], timedelta(hours=4), "4h")
    dataset.add_series("BTCUSDT", "4h", close_4h, "close")

    with pytest.raises(ValueError, match="Field 'high' not found"):
        ta.ref(dataset, timeframe="4h", field="high")


def test_resample_downsampling_close():
    dataset = Dataset()
    close_1h = _make_series(
        [100, 101, 102, 103, 104, 105],
        timedelta(hours=1),
        "1h",
    )
    dataset.add_series("BTCUSDT", "1h", close_1h, "close")

    resampled = ta.resample(
        dataset,
        from_timeframe="1h",
        to_timeframe="2h",
        field="close",
        symbol="BTCUSDT",
    )

    assert len(resampled.values) == 3
    assert resampled.values[-1] == close_1h.values[-1]


def test_resample_invalid_ratio():
    dataset = Dataset()
    close_1h = _make_series([100, 101, 102], timedelta(hours=1), "1h")
    dataset.add_series("BTCUSDT", "1h", close_1h, "close")

    with pytest.raises(ValueError):
        ta.resample(
            dataset,
            from_timeframe="1h",
            to_timeframe="90m",
            field="close",
        )
