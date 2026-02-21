from datetime import UTC, datetime
from decimal import Decimal

import pytest

import laakhay.ta as ta
from laakhay.ta.core import Dataset, Series
from laakhay.ta.core.types import Price


def make_dataset() -> Dataset:
    timestamps = [
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 2, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
    ]
    close_vals = [Price(Decimal("100")), Price(Decimal("105")), Price(Decimal("110"))]
    open_vals = [Price(Decimal("98")), Price(Decimal("104")), Price(Decimal("111"))]

    close_series = Series[Price](
        timestamps=tuple(timestamps),
        values=tuple(close_vals),
        symbol="BTCUSDT",
        timeframe="1h",
    )
    open_series = Series[Price](
        timestamps=tuple(timestamps),
        values=tuple(open_vals),
        symbol="BTCUSDT",
        timeframe="1h",
    )

    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", close_series, "close")
    ds.add_series("BTCUSDT", "1h", open_series, "open")
    return ds


def test_source_selects_field():
    dataset = make_dataset()
    close = ta.source("close")
    open_ = ta.source("open")

    close_vals = close.run(dataset)
    open_vals = open_.run(dataset)

    assert list(close_vals[("BTCUSDT", "1h", "default")].values) == [
        Price("100"),
        Price("105"),
        Price("110"),
    ]
    assert list(open_vals[("BTCUSDT", "1h", "default")].values) == [
        Price("98"),
        Price("104"),
        Price("111"),
    ]


def test_source_missing_field_raises():
    dataset = make_dataset()
    unknown = ta.source("volume")
    with pytest.raises(ValueError):
        unknown.run(dataset)
