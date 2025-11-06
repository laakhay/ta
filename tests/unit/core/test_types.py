"""Tests for laakhay.ta.core.types module."""

from datetime import date, datetime
from decimal import Decimal

from laakhay.ta.core.coercers import coerce_price, coerce_qty, coerce_rate
from laakhay.ta.core.types import (
    Price,
    PriceLike,
    Qty,
    QtyLike,
    Rate,
    RateLike,
    Symbol,
    Timestamp,
    TimestampLike,
)


class TestTypes:
    """Test type aliases."""

    def test_type_aliases(self) -> None:
        """Test that type aliases are correctly defined."""
        # Test core types
        assert Price is Decimal
        assert Qty is Decimal
        assert Rate is Decimal
        assert Symbol is str
        assert Timestamp is datetime

        # Test that they work as expected
        price: Price = Decimal("100.50")
        qty: Qty = Decimal("1000")
        rate: Rate = Decimal("5.25")
        symbol: Symbol = "BTCUSDT"
        timestamp: Timestamp = datetime(2024, 1, 1, 12, 0, 0)

        assert isinstance(price, Decimal)
        assert isinstance(qty, Decimal)
        assert isinstance(rate, Decimal)
        assert isinstance(symbol, str)
        assert isinstance(timestamp, datetime)

    def test_like_type_aliases(self) -> None:
        """Test that Like type aliases include correct types."""
        # Test PriceLike
        price_like_values = [Decimal("100"), 100, 100.5, "100.25"]
        for value in price_like_values:
            assert isinstance(value, PriceLike)

        # Test QtyLike
        qty_like_values = [Decimal("1000"), 1000, 1000.5, "1000.25"]
        for value in qty_like_values:
            assert isinstance(value, QtyLike)

        # Test RateLike
        rate_like_values = [Decimal("5"), 5, 5.5, "5.25"]
        for value in rate_like_values:
            assert isinstance(value, RateLike)

        # Test TimestampLike
        timestamp_like_values = [
            datetime(2024, 1, 1),
            "2024-01-01T12:00:00",
            1704110400,
        ]
        for value in timestamp_like_values:
            assert isinstance(value, TimestampLike)

        # Test that date is included in TimestampLike
        date_obj = date(2024, 1, 1)
        assert isinstance(date_obj, TimestampLike)

    def test_type_operations(
        self,
        sample_prices: dict[str, int | float | str | Decimal],
        sample_quantities: dict[str, int | float | str | Decimal],
        sample_rates: dict[str, int | float | str | Decimal],
    ) -> None:
        """Test that types work correctly in operations."""
        # Test Price operations
        price1 = coerce_price(sample_prices["int"])
        price2 = coerce_price(sample_prices["float"])
        result_price = price1 + price2
        assert isinstance(result_price, Decimal)
        assert result_price == Decimal("200.5")

        # Test Qty operations
        qty1 = coerce_qty(sample_quantities["int"])
        qty2 = coerce_qty(sample_quantities["float"])
        result_qty = qty1 + qty2
        assert isinstance(result_qty, Decimal)
        assert result_qty == Decimal("2000.5")

        # Test Rate operations
        rate1 = coerce_rate(sample_rates["int"])
        rate2 = coerce_rate(sample_rates["float"])
        result_rate = rate1 + rate2
        assert isinstance(result_rate, Decimal)
        assert result_rate == Decimal("10.5")


