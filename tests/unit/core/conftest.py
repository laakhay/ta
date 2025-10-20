"""Shared fixtures for core tests."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price


@pytest.fixture
def timestamp():
    """Standard timestamp for tests."""
    return datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def price_series(timestamp):
    """Standard price series for tests."""
    return Series(
        timestamps=(timestamp,),
        values=(Price(Decimal("100")),),
        symbol="TEST",
        timeframe="1s"
    )


@pytest.fixture
def multi_point_series(timestamp):
    """Multi-point price series for tests."""
    timestamp2 = datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    return Series(
        timestamps=(timestamp, timestamp2),
        values=(Price(Decimal("100")), Price(Decimal("200"))),
        symbol="TEST",
        timeframe="1s"
    )


@pytest.fixture
def different_series(timestamp):
    """Different series for testing operations."""
    timestamp2 = datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    return Series(
        timestamps=(timestamp, timestamp2),
        values=(Price(Decimal("50")), Price(Decimal("75"))),
        symbol="TEST",
        timeframe="1s"
    )
