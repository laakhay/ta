"""Shared fixtures for expressions tests."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.expressions.models import Literal, BinaryOp, UnaryOp, OperatorType
from laakhay.ta.expressions.operators import Expression, as_expression
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price


@pytest.fixture
def timestamp():
    """Standard timestamp for tests."""
    return datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def test_series(timestamp):
    """Standard test series."""
    return Series((timestamp,), (Price(Decimal("100")),), "TEST", "1s")


@pytest.fixture
def multi_point_series(timestamp):
    """Multi-point series for tests."""
    timestamp2 = datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    return Series(
        timestamps=(timestamp, timestamp2),
        values=(Price(Decimal("100")), Price(Decimal("200"))),
        symbol="TEST",
        timeframe="1s"
    )


@pytest.fixture
def literal_10():
    """Literal with value 10."""
    return Literal(10)


@pytest.fixture
def literal_20():
    """Literal with value 20."""
    return Literal(20)


@pytest.fixture
def literal_series(test_series):
    """Literal with series value."""
    return Literal(test_series)


@pytest.fixture
def binary_op_add(literal_10, literal_20):
    """Binary operation: 10 + 20."""
    return BinaryOp(literal_10, OperatorType.ADD, literal_20)


@pytest.fixture
def unary_op_neg(literal_10):
    """Unary operation: -10."""
    return UnaryOp(OperatorType.NEG, literal_10)


@pytest.fixture
def expression_10(literal_10):
    """Expression wrapping literal 10."""
    return Expression(literal_10)


@pytest.fixture
def context_dict(test_series):
    """Context dictionary for evaluation."""
    return {"price": test_series}
