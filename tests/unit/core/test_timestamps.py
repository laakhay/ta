"""Tests for laakhay.ta.core.timestamps module."""

from datetime import UTC, date, datetime

UTC = UTC

import pytest

from laakhay.ta.core.timestamps import coerce_timestamp


class TestCoerceTimestamp:
    """Test coerce_timestamp function."""

    def test_coerce_timestamp_datetime(self, sample_datetime_utc: datetime, sample_datetime_naive: datetime) -> None:
        """Test timestamp coercion with datetime objects."""
        result_utc = coerce_timestamp(sample_datetime_utc)
        assert result_utc == sample_datetime_utc
        assert result_utc.tzinfo == UTC

        # Naive datetime gets UTC timezone
        result_naive = coerce_timestamp(sample_datetime_naive)
        assert result_naive.tzinfo == UTC
        assert result_naive.replace(tzinfo=None) == sample_datetime_naive

    def test_coerce_timestamp_unix(self, sample_timestamp_unix: int, sample_datetime_utc: datetime) -> None:
        """Test timestamp coercion with Unix timestamps."""
        result = coerce_timestamp(sample_timestamp_unix)
        assert result == sample_datetime_utc
        assert result.tzinfo == UTC

        # Test negative timestamp
        negative_ts = -sample_timestamp_unix
        result_neg = coerce_timestamp(negative_ts)
        expected = datetime.fromtimestamp(negative_ts, tz=UTC)
        assert result_neg == expected

    def test_coerce_timestamp_iso_string(self, sample_iso_string: str, sample_datetime_utc: datetime) -> None:
        """Test timestamp coercion with ISO 8601 strings."""
        result = coerce_timestamp(sample_iso_string)
        assert result == sample_datetime_utc
        assert result.tzinfo == UTC

        # Test with 'Z' suffix
        iso_z = sample_iso_string.replace("+00:00", "Z")
        result_z = coerce_timestamp(iso_z)
        assert result_z == sample_datetime_utc

        # Test naive ISO string
        naive_iso = "2024-01-01T12:00:00"
        result_naive = coerce_timestamp(naive_iso)
        assert result_naive.tzinfo == UTC

    def test_coerce_timestamp_invalid(self, invalid_timestamp_strings: list[str]) -> None:
        """Test timestamp coercion with invalid inputs."""
        # Test invalid string formats
        for invalid_str in invalid_timestamp_strings:
            with pytest.raises(ValueError):
                coerce_timestamp(invalid_str)

        # Test invalid types
        with pytest.raises(TypeError):
            coerce_timestamp(None)
        with pytest.raises(TypeError):
            coerce_timestamp([])
        with pytest.raises(TypeError):
            coerce_timestamp({})

        # Float timestamps not supported
        with pytest.raises(TypeError):
            coerce_timestamp(1704110400.0)

    def test_coerce_timestamp_date(self, sample_date: date) -> None:
        """Test timestamp coercion with date objects."""
        result = coerce_timestamp(sample_date)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == UTC

    def test_coerce_timestamp_epoch_variants(self, sample_datetime_utc: datetime) -> None:
        """Test timestamp coercion with various epoch formats."""
        # Test different epoch scales
        base_ts = int(sample_datetime_utc.timestamp())

        # Seconds
        assert coerce_timestamp(base_ts) == sample_datetime_utc

        # Milliseconds
        ms_ts = base_ts * 1000
        result_ms = coerce_timestamp(ms_ts)
        assert result_ms == sample_datetime_utc

        # Microseconds
        us_ts = base_ts * 1_000_000
        result_us = coerce_timestamp(us_ts)
        assert result_us == sample_datetime_utc

        # Nanoseconds (covers line 67)
        ns_ts = base_ts * 1_000_000_000
        result_ns = coerce_timestamp(ns_ts)
        assert result_ns == sample_datetime_utc

    def test_coerce_timestamp_string_epoch(self, sample_timestamp_unix_str: str, sample_datetime_utc: datetime) -> None:
        """Test timestamp coercion with string epoch values."""
        result = coerce_timestamp(sample_timestamp_unix_str)
        assert result == sample_datetime_utc

        # Test with sign
        signed_str = f"+{sample_timestamp_unix_str}"
        result_signed = coerce_timestamp(signed_str)
        assert result_signed == sample_datetime_utc

        # Test float epoch string (covers lines 136-137)
        float_epoch_str = "1704110400.123"
        result_float = coerce_timestamp(float_epoch_str)
        expected_float = datetime.fromtimestamp(1704110400.123, tz=UTC)
        assert result_float == expected_float

    def test_coerce_timestamp_fallback_patterns(self, valid_timestamp_strings: list[str]) -> None:
        """Test timestamp coercion with various valid string formats."""
        for ts_str in valid_timestamp_strings:
            result = coerce_timestamp(ts_str)
            assert isinstance(result, datetime)
            assert result.tzinfo == UTC

        # Test fallback datetime parsing (covers line 146)
        fallback_formats = [
            "2024-01-01 12:00:00",  # %Y-%m-%d %H:%M:%S
            "2024/01/01 12:00:00",  # %Y/%m/%d %H:%M:%S
            "2024-01-01 12:00:00.123",  # %Y-%m-%d %H:%M:%S.%f
            "2024/01/01 12:00:00.123",  # %Y/%m/%d %H:%M:%S.%f
            "2024-01-01",  # %Y-%m-%d (date-only)
        ]

        for fmt_str in fallback_formats:
            result = coerce_timestamp(fmt_str)
            assert isinstance(result, datetime)
            assert result.tzinfo == UTC

    def test_coerce_timestamp_edge_cases(self, sample_datetime_utc: datetime) -> None:
        """Test edge cases for timestamp coercion."""
        # Test empty string
        with pytest.raises(ValueError, match="Invalid timestamp: empty string"):
            coerce_timestamp("")

        # Test string with only whitespace
        with pytest.raises(ValueError, match="Invalid timestamp: empty string"):
            coerce_timestamp("   ")

        # Test string that becomes empty after stripping
        with pytest.raises(ValueError, match="Invalid timestamp: empty string"):
            coerce_timestamp(" \t\n ")

        # Test string that has whitespace but becomes empty in _is_integerish
        with pytest.raises(ValueError, match="Invalid timestamp string"):
            coerce_timestamp("   abc")  # This will call _is_integerish but fail

        # Test non-integer string that should trigger _is_integerish return False
        with pytest.raises(ValueError, match="Invalid timestamp string"):
            coerce_timestamp("abc123")

        # Test signed integer strings
        base_ts = int(sample_datetime_utc.timestamp())

        # Positive sign
        assert coerce_timestamp(f"+{base_ts}") == sample_datetime_utc

        # Negative sign
        negative_ts = -base_ts
        result = coerce_timestamp(str(negative_ts))
        expected = datetime.fromtimestamp(negative_ts, tz=UTC)
        assert result == expected

        # Test date object (covers line 112)
        from datetime import date

        date_obj = date(2024, 1, 1)
        result = coerce_timestamp(date_obj)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == UTC
