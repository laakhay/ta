"""Shared test fixtures for laakhay.ta tests."""

import pytest
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Any, Dict, List, Union


@pytest.fixture
def sample_datetime_utc() -> datetime:
    """Sample UTC datetime for testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


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
def sample_prices() -> Dict[str, Union[int, float, str, Decimal]]:
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
def sample_quantities() -> Dict[str, Union[int, float, str, Decimal]]:
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
def sample_rates() -> Dict[str, Union[int, float, str, Decimal]]:
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
def sample_bar_data() -> Dict[str, Any]:
    """Sample bar data for testing."""
    return {
        "ts": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "open": 100,
        "high": 110,
        "low": 95,
        "close": 105,
        "volume": 1000,
        "is_closed": True,
    }


@pytest.fixture
def sample_bar_dict() -> Dict[str, Any]:
    """Sample bar data as dictionary for testing."""
    return {
        "ts": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "open": 100,
        "high": 110,
        "low": 95,
        "close": 105,
        "volume": 1000,
        "is_closed": True,
    }


@pytest.fixture
def sample_bar_dict_alternative_keys() -> Dict[str, Any]:
    """Sample bar data with alternative key names for testing."""
    return {
        "timestamp": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "open_price": 100,
        "high_price": 110,
        "low_price": 95,
        "close_price": 105,
        "volume_qty": 1000,
        "closed": True,
    }


@pytest.fixture
def sample_bar_dict_short_keys() -> Dict[str, Any]:
    """Sample bar data with short key names for testing."""
    return {
        "ts": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "o": 100,
        "h": 110,
        "l": 95,
        "c": 105,
        "v": 1000,
        "x": True,
    }


@pytest.fixture
def invalid_timestamp_strings() -> List[str]:
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
def invalid_numeric_values() -> List[Any]:
    """Invalid numeric values for testing error cases."""
    return [
        None,
        [],
        {},
        "not_a_number",
        "12.34.56",
    ]


@pytest.fixture
def valid_timestamp_strings() -> List[str]:
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
def valid_numeric_strings() -> List[str]:
    """Valid numeric strings for testing."""
    return [
        "100",
        "100.5",
        "+100",
        "-100",
        "0",
        "0.0",
    ]
