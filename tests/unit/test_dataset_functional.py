"""Functional tests for the Dataset API."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta import Bar, Price, dataset
from laakhay.ta.core import OHLCV, Series
from laakhay.ta.core.types import Price


class TestDatasetFunctional:
    """Test Dataset with real data and user-friendly API."""

    def test_dataset_from_bars(self):
        """Test creating dataset from bars."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Test that dataset has the OHLCV
        assert len(ds._series) == 1
        assert not ds.is_empty

    def test_dataset_field_access(self):
        """Test accessing OHLCV fields through dataset."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Test field access
        close_series = ds["close"]
        open_series = ds["open"]
        high_series = ds["high"]
        low_series = ds["low"]
        volume_series = ds["volume"]

        # Verify close series
        assert isinstance(close_series, Series)
        assert len(close_series.values) == 2
        assert close_series.values[0] == Price(Decimal("102"))
        assert close_series.values[1] == Price(Decimal("106"))

        # Verify open series
        assert isinstance(open_series, Series)
        assert len(open_series.values) == 2
        assert open_series.values[0] == Price(Decimal("100"))
        assert open_series.values[1] == Price(Decimal("102"))

        # Verify high series
        assert isinstance(high_series, Series)
        assert len(high_series.values) == 2
        assert high_series.values[0] == Price(Decimal("105"))
        assert high_series.values[1] == Price(Decimal("108"))

        # Verify low series
        assert isinstance(low_series, Series)
        assert len(low_series.values) == 2
        assert low_series.values[0] == Price(Decimal("95"))
        assert low_series.values[1] == Price(Decimal("98"))

        # Verify volume series
        assert isinstance(volume_series, Series)
        assert len(volume_series.values) == 2
        assert volume_series.values[0] == Price(Decimal("1000"))
        assert volume_series.values[1] == Price(Decimal("1200"))

    def test_dataset_invalid_field_access(self):
        """Test error handling for invalid field access."""
        # Create empty dataset
        ds = dataset()

        # Test accessing field on empty dataset
        with pytest.raises(KeyError, match="No series found in dataset"):
            _ = ds["close"]

        # Test accessing invalid field
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True
            ),
        ]

        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")
        ds = dataset(ohlcv)

        with pytest.raises(KeyError, match="No series found with symbol: invalid"):
            _ = ds["invalid"]

    def test_dataset_with_multiple_series(self):
        """Test dataset with multiple series."""
        # Create two different OHLCV series
        bars1 = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True
            ),
        ]

        bars2 = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("200"),
                high=Price("210"),
                low=Price("190"),
                close=Price("205"),
                volume=Price("2000"),
                is_closed=True
            ),
        ]

        ohlcv1 = OHLCV.from_bars(bars1, symbol="BTCUSDT", timeframe="1h")
        ohlcv2 = OHLCV.from_bars(bars2, symbol="ETHUSDT", timeframe="1h")

        # Create dataset with both series
        ds = dataset(ohlcv1, ohlcv2)

        # Test accessing by symbol
        btc_series = ds["BTCUSDT"]
        eth_series = ds["ETHUSDT"]

        assert isinstance(btc_series, OHLCV)
        assert isinstance(eth_series, OHLCV)
        assert btc_series.symbol == "BTCUSDT"
        assert eth_series.symbol == "ETHUSDT"

        # Test field access (should get from first series)
        close_series = ds["close"]
        assert isinstance(close_series, Series)
        assert close_series.values[0] == Price(Decimal("102"))  # BTCUSDT close

    def test_dataset_empty(self):
        """Test empty dataset behavior."""
        ds = dataset()

        assert ds.is_empty
        assert len(ds._series) == 0
        assert len(ds) == 0
