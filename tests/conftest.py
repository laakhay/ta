"""Shared test fixtures for laakhay.ta tests."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def ensure_indicators_registered():
    """Ensure indicators are registered before each test."""
    # Force import of indicators to trigger registration
    from laakhay.ta import indicators  # noqa: F401

    yield

@pytest.fixture
def sample_datetime_utc() -> datetime:
    """Sample UTC datetime for testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_datetime_naive() -> datetime:
    """Sample naive datetime for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def sample_date() -> date:
    """Sample date object for testing."""
    return date(2024, 1, 1)


@pytest.fixture
def sample_timestamp_unix() -> int:
    """Sample Unix timestamp (int) for testing."""
    return 1704110400  # 2024-01-01 12:00:00 UTC


@pytest.fixture
def sample_timestamp_unix_str() -> str:
    """Sample Unix timestamp as string for testing."""
    return "1704110400"


@pytest.fixture
def sample_iso_string() -> str:
    """Sample ISO 8601 string for testing."""
    return "2024-01-01T12:00:00+00:00"


@pytest.fixture
def sample_prices() -> dict[str, int | float | str | Decimal]:
    """Sample price values for testing."""
    return {
        "int": 100,
        "float": 100.5,
        "str": "100.25",
        "decimal": Decimal("100.75"),
        "zero": 0,
        "negative": -1,
    }


@pytest.fixture
def sample_quantities() -> dict[str, int | float | str | Decimal]:
    """Sample quantity values for testing."""
    return {
        "int": 1000,
        "float": 1000.5,
        "str": "1000.25",
        "decimal": Decimal("1000.75"),
        "zero": 0,
        "negative": -1,
    }


@pytest.fixture
def sample_rates() -> dict[str, int | float | str | Decimal]:
    """Sample rate values for testing."""
    return {
        "int": 5,
        "float": 5.5,
        "str": "5.25",
        "decimal": Decimal("5.75"),
        "zero": 0,
        "negative": -1,
    }


@pytest.fixture
def sample_bar_data() -> dict[str, Any]:
    """Sample bar data for testing."""
    return {
        "ts": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        "open": 100,
        "high": 110,
        "low": 95,
        "close": 105,
        "volume": 1000,
        "is_closed": True,
    }


@pytest.fixture
def sample_bar_dict() -> dict[str, Any]:
    """Sample bar data as dictionary for testing."""
    return {
        "ts": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        "open": 100,
        "high": 110,
        "low": 95,
        "close": 105,
        "volume": 1000,
        "is_closed": True,
    }


@pytest.fixture
def sample_bar_dict_alternative_keys() -> dict[str, Any]:
    """Sample bar data with alternative key names for testing."""
    return {
        "timestamp": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        "open_price": 100,
        "high_price": 110,
        "low_price": 95,
        "close_price": 105,
        "volume_qty": 1000,
        "closed": True,
    }


@pytest.fixture
def sample_bar_dict_short_keys() -> dict[str, Any]:
    """Sample bar data with short key names for testing."""
    return {
        "ts": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        "o": 100,
        "h": 110,
        "l": 95,
        "c": 105,
        "v": 1000,
        "x": True,
    }


@pytest.fixture
def invalid_timestamp_strings() -> list[str]:
    """Invalid timestamp strings for testing error cases."""
    return [
        "",
        "   ",
        " \t\n ",
        "abc123",
        "01-01-2024 12:00:00",
        "invalid",
        "12.34.56",
    ]


@pytest.fixture
def invalid_numeric_values() -> list[Any]:
    """Invalid numeric values for testing error cases."""
    return [
        None,
        [],
        {},
        "not_a_number",
        "12.34.56",
    ]


@pytest.fixture
def valid_timestamp_strings() -> list[str]:
    """Valid timestamp strings for testing."""
    return [
        "2024-01-01T12:00:00+00:00",
        "2024-01-01T12:00:00Z",
        "2024-01-01 12:00:00",
        "1704110400",
        "+1704110400",
        "-1704110400",
    ]


@pytest.fixture
def valid_numeric_strings() -> list[str]:
    """Valid numeric strings for testing."""
    return [
        "100",
        "100.5",
        "+100",
        "-100",
        "0",
        "0.0",
    ]

# Series and OHLCV test fixtures
@pytest.fixture
def sample_timestamps() -> tuple[datetime, ...]:
    """Sample timestamps for testing."""
    base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    return (
        base_time,
        base_time + timedelta(hours=1),
        base_time + timedelta(hours=2),
        base_time + timedelta(hours=3),
    )

@pytest.fixture
def sample_price_values() -> tuple[Decimal, ...]:
    """Sample price values for testing."""
    return (
        Decimal("100.00"),
        Decimal("101.50"),
        Decimal("99.75"),
        Decimal("102.25"),
    )

@pytest.fixture
def sample_volumes() -> tuple[Decimal, ...]:
    """Sample volumes for testing."""
    return (
        Decimal("1000"),
        Decimal("1500"),
        Decimal("800"),
        Decimal("1200"),
    )

@pytest.fixture
def sample_series_data(sample_timestamps: tuple[datetime, ...], sample_price_values: tuple[Decimal, ...]) -> dict[str, Any]:
    """Sample series data for testing."""
    return {
        "timestamps": sample_timestamps,
        "values": sample_price_values,
        "symbol": "BTCUSDT",
        "timeframe": "1h"
    }

@pytest.fixture
def sample_ohlcv_data(sample_timestamps: tuple[datetime, ...], sample_price_values: tuple[Decimal, ...], sample_volumes: tuple[Decimal, ...]) -> dict[str, Any]:
    """Sample OHLCV data for testing."""
    return {
        "timestamps": sample_timestamps,
        "opens": sample_price_values,
        "highs": sample_price_values,
        "lows": sample_price_values,
        "closes": sample_price_values,
        "volumes": sample_volumes,
        "is_closed": (True, True, True, True),
        "symbol": "BTCUSDT",
        "timeframe": "1h"
    }

@pytest.fixture
def sample_bars(sample_timestamps: tuple[datetime, ...], sample_price_values: tuple[Decimal, ...], sample_volumes: tuple[Decimal, ...]) -> list[Any]:
    """Sample Bar objects for testing."""
    from laakhay.ta.core.bar import Bar
    return [
        Bar(
            ts=sample_timestamps[i],
            open=sample_price_values[i],
            high=sample_price_values[i],
            low=sample_price_values[i],
            close=sample_price_values[i],
            volume=sample_volumes[i],
            is_closed=True
        )
        for i in range(len(sample_timestamps))
    ]

@pytest.fixture
def empty_series_data() -> dict[str, Any]:
    """Empty series data for testing."""
    return {
        "timestamps": (),
        "values": (),
        "symbol": "BTCUSDT",
        "timeframe": "1h"
    }

@pytest.fixture
def unsorted_timestamps() -> tuple[datetime, ...]:
    """Unsorted timestamps for testing validation."""
    base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    return (
        base_time + timedelta(hours=2),
        base_time,
        base_time + timedelta(hours=1),
    )
