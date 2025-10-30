"""Tests for ta.load.csv functionality."""

import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from laakhay.ta.core import OHLCV, Series
from laakhay.ta.io.csv import from_csv


class TestLoadCSV:
    """Test CSV loading functionality."""

    def test_load_ohlcv_csv(self) -> None:
        """Test loading OHLCV data from CSV."""
        # Create temporary CSV file
        csv_content = """timestamp,open,high,low,close,volume,is_closed
2024-01-01T00:00:00Z,100.0,101.0,99.0,100.5,1000,true
2024-01-01T01:00:00Z,100.5,102.0,100.0,101.5,1100,true"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # Load OHLCV data
            ohlcv = from_csv(temp_path, symbol="BTCUSDT", timeframe="1h")

            assert isinstance(ohlcv, OHLCV)
            assert len(ohlcv) == 2
            assert ohlcv.symbol == "BTCUSDT"
            assert ohlcv.timeframe == "1h"
            assert ohlcv.opens[0] == Decimal("100.0")
            assert ohlcv.closes[0] == Decimal("100.5")
            assert ohlcv.is_closed[0] is True

        finally:
            Path(temp_path).unlink()

    def test_load_series_csv(self) -> None:
        """Test loading Series data from CSV."""
        # Create temporary CSV file with price data
        csv_content = """timestamp,price
2024-01-01T00:00:00Z,100.0
2024-01-01T01:00:00Z,100.5
2024-01-01T02:00:00Z,101.0"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # Load Series data
            series = from_csv(temp_path, symbol="BTCUSDT", timeframe="1h", value_col="price")

            assert isinstance(series, Series)
            assert len(series) == 3
            assert series.symbol == "BTCUSDT"
            assert series.timeframe == "1h"
            assert series.values[0] == Decimal("100.0")
            assert series.values[1] == Decimal("100.5")

        finally:
            Path(temp_path).unlink()

    def test_from_csv_with_custom_columns(self) -> None:
        """Test loading CSV with custom column mappings."""
        csv_content = """time,o,h,l,c,v,closed
2024-01-01T00:00:00Z,100.0,101.0,99.0,100.5,1000,true
2024-01-01T01:00:00Z,100.5,102.0,100.0,101.5,1100,false"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # Load with custom column mappings
            ohlcv = from_csv(
                temp_path,
                symbol="ETHUSDT",
                timeframe="5m",
                timestamp_col="time",
                open_col="o",
                high_col="h",
                low_col="l",
                close_col="c",
                volume_col="v",
                is_closed_col="closed"
            )

            assert isinstance(ohlcv, OHLCV)
            assert len(ohlcv) == 2
            assert ohlcv.symbol == "ETHUSDT"
            assert ohlcv.timeframe == "5m"
            assert ohlcv.is_closed[1] is False

        finally:
            Path(temp_path).unlink()

    def test_from_csv_missing_file(self) -> None:
        """Test loading non-existent CSV file."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            from_csv("nonexistent.csv", symbol="BTCUSDT", timeframe="1h")

    def test_from_csv_empty_file(self) -> None:
        """Test loading empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="CSV file is empty or has no headers"):
                from_csv(temp_path, symbol="BTCUSDT", timeframe="1h")
        finally:
            Path(temp_path).unlink()

    def test_from_csv_missing_timestamp_column(self) -> None:
        """Test loading CSV with missing timestamp column."""
        csv_content = """open,high,low,close,volume
100.0,101.0,99.0,100.5,1000"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Timestamp column 'timestamp' not found in CSV"):
                from_csv(temp_path, symbol="BTCUSDT", timeframe="1h")
        finally:
            Path(temp_path).unlink()

    def test_from_csv_missing_value_column(self) -> None:
        """Test loading Series CSV with missing value column."""
        csv_content = """timestamp
2024-01-01T00:00:00Z"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Value column 'value' not found in CSV"):
                from_csv(temp_path, symbol="BTCUSDT", timeframe="1h")
        finally:
            Path(temp_path).unlink()

    def test_from_csv_invalid_data(self) -> None:
        """Test loading CSV with invalid data."""
        csv_content = """timestamp,open,high,low,close,volume
2024-01-01T00:00:00Z,invalid,101.0,99.0,100.5,1000"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Error parsing row 2.*Invalid numeric data"):
                from_csv(temp_path, symbol="BTCUSDT", timeframe="1h")
        finally:
            Path(temp_path).unlink()

    def test_from_csv_default_is_closed(self) -> None:
        """Test loading OHLCV CSV with default is_closed values."""
        csv_content = """timestamp,open,high,low,close,volume
2024-01-01T00:00:00Z,100.0,101.0,99.0,100.5,1000
2024-01-01T01:00:00Z,100.5,102.0,100.0,101.5,1100"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            ohlcv = from_csv(temp_path, symbol="BTCUSDT", timeframe="1h")

            assert isinstance(ohlcv, OHLCV)
            assert all(ohlcv.is_closed)  # Should default to True

        finally:
            Path(temp_path).unlink()

    def test_from_csv_various_is_closed_formats(self) -> None:
        """Test loading CSV with various is_closed value formats."""
        csv_content = """timestamp,open,high,low,close,volume,is_closed
2024-01-01T00:00:00Z,100.0,101.0,99.0,100.5,1000,true
2024-01-01T01:00:00Z,100.5,102.0,100.0,101.5,1100,1
2024-01-01T02:00:00Z,101.0,103.0,100.5,102.5,1200,yes
2024-01-01T03:00:00Z,102.5,104.0,102.0,103.5,1300,closed
2024-01-01T04:00:00Z,103.5,105.0,103.0,104.5,1400,false"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            ohlcv = from_csv(temp_path, symbol="BTCUSDT", timeframe="1h")

            assert isinstance(ohlcv, OHLCV)
            assert len(ohlcv) == 5
            assert ohlcv.is_closed[0] is True  # "true"
            assert ohlcv.is_closed[1] is True  # "1"
            assert ohlcv.is_closed[2] is True  # "yes"
            assert ohlcv.is_closed[3] is True  # "closed"
            assert ohlcv.is_closed[4] is False  # "false"

        finally:
            Path(temp_path).unlink()
