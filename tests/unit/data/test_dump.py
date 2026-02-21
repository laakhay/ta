"""Tests for ta.dump.csv functionality."""

import tempfile
from datetime import timezone, datetime
UTC = timezone.utc
from decimal import Decimal
from pathlib import Path

import pytest

from laakhay.ta.core import OHLCV, Series
from laakhay.ta.core.types import Price
from laakhay.ta.data.csv import to_csv


class TestDumpCSV:
    """Test CSV dumping functionality."""

    @pytest.fixture
    def sample_ohlcv(self) -> OHLCV:
        """Sample OHLCV data for testing."""
        timestamps = (
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 1, 1, 1, 0, 0, tzinfo=UTC),
        )
        return OHLCV(
            timestamps=timestamps,
            opens=(Decimal("100.0"), Decimal("100.5")),
            highs=(Decimal("101.0"), Decimal("102.0")),
            lows=(Decimal("99.0"), Decimal("100.0")),
            closes=(Decimal("100.5"), Decimal("101.5")),
            volumes=(Decimal("1000"), Decimal("1100")),
            is_closed=(True, False),
            symbol="BTCUSDT",
            timeframe="1h",
        )

    @pytest.fixture
    def sample_series(self) -> Series[Price]:
        """Sample Series data for testing."""
        timestamps = (
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 1, 1, 1, 0, 0, tzinfo=UTC),
            datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC),
        )
        return Series[Price](
            timestamps=timestamps,
            values=(Decimal("100.0"), Decimal("100.5"), Decimal("101.0")),
            symbol="BTCUSDT",
            timeframe="1h",
        )

    def test_dump_ohlcv_csv(self, sample_ohlcv: OHLCV) -> None:
        """Test dumping OHLCV data to CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Dump OHLCV data
            to_csv(sample_ohlcv, temp_path)

            # Verify CSV content
            with open(temp_path) as f:
                lines = f.readlines()

            assert len(lines) == 3  # Header + 2 data rows
            assert "timestamp,open,high,low,close,volume,is_closed" in lines[0]
            assert "2024-01-01T00:00:00+00:00,100.0,101.0,99.0,100.5,1000,True" in lines[1]
            assert "2024-01-01T01:00:00+00:00,100.5,102.0,100.0,101.5,1100,False" in lines[2]

        finally:
            Path(temp_path).unlink()

    def test_dump_series_csv(self, sample_series: Series[Price]) -> None:
        """Test dumping Series data to CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Dump Series data
            to_csv(sample_series, temp_path)

            # Verify CSV content
            with open(temp_path) as f:
                lines = f.readlines()

            assert len(lines) == 4  # Header + 3 data rows
            assert "timestamp,value" in lines[0]
            assert "2024-01-01T00:00:00+00:00,100.0" in lines[1]
            assert "2024-01-01T01:00:00+00:00,100.5" in lines[2]
            assert "2024-01-01T02:00:00+00:00,101.0" in lines[3]

        finally:
            Path(temp_path).unlink()

    def test_to_csv_with_custom_columns(self, sample_ohlcv: OHLCV) -> None:
        """Test dumping CSV with custom column mappings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Dump with custom column mappings
            to_csv(
                sample_ohlcv,
                temp_path,
                timestamp_col="time",
                open_col="o",
                high_col="h",
                low_col="l",
                close_col="c",
                volume_col="v",
                is_closed_col="closed",
            )

            # Verify CSV content
            with open(temp_path) as f:
                lines = f.readlines()

            assert len(lines) == 3  # Header + 2 data rows
            assert "time,o,h,l,c,v,closed" in lines[0]
            assert "2024-01-01T00:00:00+00:00,100.0,101.0,99.0,100.5,1000,True" in lines[1]

        finally:
            Path(temp_path).unlink()

    def test_to_csv_creates_directory(self, sample_ohlcv: OHLCV) -> None:
        """Test that to_csv creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "output.csv"

            # Should create the subdir directory
            to_csv(sample_ohlcv, output_path)

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_to_csv_invalid_data_type(self) -> None:
        """Test dumping invalid data type."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(AttributeError):
                to_csv("invalid_data", temp_path)  # type: ignore[arg-type]
        finally:
            Path(temp_path).unlink()

    def test_to_csv_empty_ohlcv(self) -> None:
        """Test dumping empty OHLCV data."""
        empty_ohlcv = OHLCV(
            timestamps=(),
            opens=(),
            highs=(),
            lows=(),
            closes=(),
            volumes=(),
            is_closed=(),
            symbol="BTCUSDT",
            timeframe="1h",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            to_csv(empty_ohlcv, temp_path)

            # Verify CSV content (should only have header)
            with open(temp_path) as f:
                lines = f.readlines()

            assert len(lines) == 1  # Only header
            assert "timestamp,open,high,low,close,volume,is_closed" in lines[0]

        finally:
            Path(temp_path).unlink()

    def test_to_csv_empty_series(self) -> None:
        """Test dumping empty Series data."""
        empty_series = Series[Price](timestamps=(), values=(), symbol="BTCUSDT", timeframe="1h")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            to_csv(empty_series, temp_path)

            # Verify CSV content (should only have header)
            with open(temp_path) as f:
                lines = f.readlines()

            assert len(lines) == 1  # Only header
            assert "timestamp,value" in lines[0]

        finally:
            Path(temp_path).unlink()


class TestCSVExportCriticalIssues:
    """Test critical issues with CSV export identified in the audit."""

    def test_csv_export_preserves_decimal_precision(self):
        """Test that CSV export preserves Decimal precision."""
        import os

        from laakhay.ta.data.csv import from_csv

        # Create series with Decimal values
        series = Series[Price](
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
            values=(Price(Decimal("100.123456789")),),  # High precision decimal
            symbol="BTC",
            timeframe="1h",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Export to CSV
            to_csv(series, temp_path)

            # Import back from CSV
            imported_series = from_csv(temp_path, "BTC", "1h")

            # This should work - precision should be preserved
            assert imported_series.values[0] == Price(Decimal("100.123456789")), "Decimal precision should be preserved"

        finally:
            os.unlink(temp_path)

    def test_csv_export_ohlcv_preserves_decimal_precision(self):
        """Test that OHLCV CSV export preserves Decimal precision."""
        import os

        from laakhay.ta.core.types import Qty
        from laakhay.ta.data.csv import from_csv

        ohlcv = OHLCV(
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
            opens=(Price(Decimal("100.123456789")),),
            highs=(Price(Decimal("101.123456789")),),
            lows=(Price(Decimal("99.123456789")),),
            closes=(Price(Decimal("100.123456789")),),
            volumes=(Qty(Decimal("1000.123456789")),),
            is_closed=(True,),
            symbol="BTC",
            timeframe="1h",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Export to CSV
            to_csv(ohlcv, temp_path)

            # Import back from CSV
            imported_ohlcv = from_csv(temp_path, "BTC", "1h")

            # This should work - precision should be preserved
            assert imported_ohlcv.opens[0] == Price(Decimal("100.123456789")), (
                "Open price precision should be preserved"
            )
            assert imported_ohlcv.volumes[0] == Qty(Decimal("1000.123456789")), "Volume precision should be preserved"

        finally:
            os.unlink(temp_path)
