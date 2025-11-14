from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta.dataset import dataset_from_bars, trim_dataset


def sample_bars():
    base = datetime(2024, 1, 1, tzinfo=UTC)
    return [
        {
            "timestamp": base,
            "open": "100.0",
            "high": Decimal("101"),
            "low": 99,
            "close": 100.5,
            "volume": "1500",
            "is_closed": True,
        },
        {
            "timestamp": base.replace(hour=1),
            "open": "101.0",
            "high": Decimal("102"),
            "low": 100,
            "close": 101.5,
            "volume": "1600",
            "is_closed": True,
        },
    ]


def test_dataset_from_bars_normalizes_numeric_values():
    dataset = dataset_from_bars(sample_bars(), symbol="BTCUSDT", timeframe="1h")
    series = dataset.series("BTCUSDT", "1h")
    assert series is not None
    assert series.length == 2
    assert float(series.opens[0]) == 100.0
    assert float(series.highs[1]) == 102.0


def test_trim_dataset_reduces_length():
    dataset = dataset_from_bars(sample_bars(), symbol="BTCUSDT", timeframe="1h")
    trimmed = trim_dataset(dataset, symbol="BTCUSDT", timeframe="1h", trim=1)
    series = trimmed.series("BTCUSDT", "1h")
    assert series is not None
    assert series.length == 1


def test_trim_dataset_empty_error():
    dataset = dataset_from_bars(sample_bars(), symbol="BTCUSDT", timeframe="1h")
    with pytest.raises(ValueError):
        trim_dataset(dataset, symbol="BTCUSDT", timeframe="1h", trim=10)
