"""Shared fixtures for registry tests."""

from datetime import UTC, datetime
from decimal import Decimal
from inspect import signature

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.registry.models import IndicatorHandle, SeriesContext
from laakhay.ta.registry.registry import Registry
from laakhay.ta.registry.schemas import IndicatorSchema, ParamSchema


@pytest.fixture
def timestamp():
    """Standard timestamp for tests."""
    return datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)


@pytest.fixture
def test_series(timestamp):
    """Standard test series."""
    return Series((timestamp,), (Price(Decimal("100")),), "TEST", "1s")


@pytest.fixture
def series_context(test_series):
    """Standard series context."""
    return SeriesContext(price_series=test_series)


@pytest.fixture
def registry():
    """Fresh registry instance."""
    return Registry()


@pytest.fixture
def param_schema():
    """Standard parameter schema."""
    return ParamSchema(
        name="test_param",
        type=float,
        required=True,
        description="Test parameter"
    )


@pytest.fixture
def indicator_schema(param_schema):
    """Standard indicator schema."""
    return IndicatorSchema(
        name="test_indicator",
        description="Test indicator",
        parameters={"test_param": param_schema},
        outputs={}
    )


@pytest.fixture
def test_function():
    """Standard test function."""
    def func(ctx: SeriesContext, test_param: float) -> Series[Price]:
        return Series((), (), "TEST", "1s")
    return func


@pytest.fixture
def indicator_handle(test_function, indicator_schema):
    """Standard indicator handle."""
    return IndicatorHandle(
        name="test_indicator",
        func=test_function,
        signature=signature(test_function),
        schema=indicator_schema,
        aliases=[]
    )
