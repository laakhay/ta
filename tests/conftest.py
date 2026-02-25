from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, Union

import pytest

UTC = UTC


@pytest.fixture(autouse=True)
def ensure_indicators_registered():
    """Ensure indicators are registered before each test.

    This fixture runs before each test to ensure indicators are registered.
    If the registry was cleared by a previous test, it will re-import the
    indicators module to re-register them.
    """
    from laakhay.ta.registry.registry import get_global_registry

    registry = get_global_registry()

    # Check if common indicators are already registered
    common_indicators = ["sma", "ema", "rsi", "select"]
    has_common = any(name in registry._indicators for name in common_indicators)

    if not has_common:
        # Registry was likely cleared - need to re-register
        import importlib
        import sys

        # Clear the indicators module and submodules from cache to force re-execution
        module_name = "laakhay.ta.indicators"
        modules_to_clear = [
            key for key in list(sys.modules.keys()) if key == module_name or key.startswith(f"{module_name}.")
        ]
        for key in modules_to_clear:
            del sys.modules[key]

        # Re-import which will re-execute decorators and register indicators
        importlib.import_module(module_name)

        # Also ensure namespace helpers are registered
        from laakhay.ta.api.namespace import ensure_namespace_registered

        ensure_namespace_registered()
    else:
        # Indicators exist - just ensure namespace helpers are registered
        from laakhay.ta.api.namespace import ensure_namespace_registered

        ensure_namespace_registered()

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
def sample_prices() -> dict[str, Union[int, float, str, Decimal]]:
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
def sample_quantities() -> dict[str, Union[int, float, str, Decimal]]:
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
def sample_rates() -> dict[str, Union[int, float, str, Decimal]]:
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
def sample_series_data(
    sample_timestamps: tuple[datetime, ...], sample_price_values: tuple[Decimal, ...]
) -> dict[str, Any]:
    """Sample series data for testing."""
    return {
        "timestamps": sample_timestamps,
        "values": sample_price_values,
        "symbol": "BTCUSDT",
        "timeframe": "1h",
    }


@pytest.fixture
def sample_ohlcv_data(
    sample_timestamps: tuple[datetime, ...],
    sample_price_values: tuple[Decimal, ...],
    sample_volumes: tuple[Decimal, ...],
) -> dict[str, Any]:
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
        "timeframe": "1h",
    }


@pytest.fixture
def sample_bars(
    sample_timestamps: tuple[datetime, ...],
    sample_price_values: tuple[Decimal, ...],
    sample_volumes: tuple[Decimal, ...],
) -> list[Any]:
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
            is_closed=True,
        )
        for i in range(len(sample_timestamps))
    ]


@pytest.fixture
def empty_series_data() -> dict[str, Any]:
    """Empty series data for testing."""
    return {"timestamps": (), "values": (), "symbol": "BTCUSDT", "timeframe": "1h"}


@pytest.fixture
def unsorted_timestamps() -> tuple[datetime, ...]:
    """Unsorted timestamps for testing validation."""
    base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    return (
        base_time + timedelta(hours=2),
        base_time,
        base_time + timedelta(hours=1),
    )


@pytest.fixture
def multi_source_dataset() -> Any:
    """Create a comprehensive multi-source dataset fixture for testing."""
    from datetime import datetime, timedelta
    from decimal import Decimal

    from laakhay.ta.core.bar import Bar
    from laakhay.ta.core.dataset import Dataset
    from laakhay.ta.core.ohlcv import OHLCV
    from laakhay.ta.core.series import Series
    from laakhay.ta.core.types import Price

    base = datetime(2024, 1, 1, tzinfo=UTC)

    # OHLCV data
    bars = [
        Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i * 100, True)
        for i in range(50)
    ]
    ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

    # Trades aggregation data
    trades_volume = Series[Price](
        timestamps=tuple(base + timedelta(hours=i) for i in range(50)),
        values=tuple(Price(Decimal(5000 + i * 100)) for i in range(50)),
        symbol="BTCUSDT",
        timeframe="1h",
    )

    trades_count = Series[int](
        timestamps=tuple(base + timedelta(hours=i) for i in range(50)),
        values=tuple(100 + i * 10 for i in range(50)),
        symbol="BTCUSDT",
        timeframe="1h",
    )

    # Orderbook data
    orderbook_imbalance = Series[Price](
        timestamps=tuple(base + timedelta(hours=i) for i in range(50)),
        values=tuple(Price(Decimal(0.4 + (i % 10) * 0.02)) for i in range(50)),
        symbol="BTCUSDT",
        timeframe="1h",
    )

    orderbook_spread = Series[Price](
        timestamps=tuple(base + timedelta(hours=i) for i in range(50)),
        values=tuple(Price(Decimal(0.5 + i * 0.01)) for i in range(50)),
        symbol="BTCUSDT",
        timeframe="1h",
    )

    # Liquidation data
    liquidation_volume = Series[Price](
        timestamps=tuple(base + timedelta(hours=i) for i in range(50)),
        values=tuple(Price(Decimal(100 + i * 10)) for i in range(50)),
        symbol="BTCUSDT",
        timeframe="1h",
    )

    liquidation_count = Series[int](
        timestamps=tuple(base + timedelta(hours=i) for i in range(50)),
        values=tuple(5 + i for i in range(50)),
        symbol="BTCUSDT",
        timeframe="1h",
    )

    # Build dataset
    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", ohlcv, source="ohlcv")
    ds.add_trade_series("BTCUSDT", "1h", trades_volume)
    ds.add_series("BTCUSDT", "1h", orderbook_imbalance, source="orderbook_imbalance")
    ds.add_liquidation_series("BTCUSDT", "1h", liquidation_volume)
    ds.add_series("BTCUSDT", "1h", trades_count, source="trades")
    ds.add_series("BTCUSDT", "1h", orderbook_spread, source="orderbook_spread")
    ds.add_series("BTCUSDT", "1h", liquidation_count, source="liquidation")

    return ds
