"""Tests for laakhay.ta.core.coercers module."""

from decimal import Decimal

import pytest

from laakhay.ta.core.coercers import coerce_price, coerce_qty, coerce_rate


class TestCoercers:
    """Test coercion functions."""

    def test_coerce_price(self, sample_prices: dict[str, int | float | str | Decimal]) -> None:
        """Test price coercion with various inputs."""
        assert coerce_price(sample_prices["int"]) == Decimal("100")
        assert coerce_price(sample_prices["float"]) == Decimal("100.5")
        assert coerce_price(sample_prices["str"]) == Decimal("100.25")
        assert coerce_price(sample_prices["decimal"]) == Decimal("100.75")
        assert coerce_price(sample_prices["zero"]) == Decimal("0")
        assert coerce_price(sample_prices["negative"]) == Decimal("-1")  # No validation

        # Test invalid types
        with pytest.raises(TypeError, match="Invalid price value"):
            coerce_price(None)
        with pytest.raises(TypeError, match="Invalid price value"):
            coerce_price([])
        with pytest.raises(TypeError, match="Invalid price value"):
            coerce_price({})

    def test_coerce_qty(self, sample_quantities: dict[str, int | float | str | Decimal]) -> None:
        """Test quantity coercion with various inputs."""
        assert coerce_qty(sample_quantities["int"]) == Decimal("1000")
        assert coerce_qty(sample_quantities["float"]) == Decimal("1000.5")
        assert coerce_qty(sample_quantities["str"]) == Decimal("1000.25")
        assert coerce_qty(sample_quantities["decimal"]) == Decimal("1000.75")
        assert coerce_qty(sample_quantities["zero"]) == Decimal("0")
        assert coerce_qty(sample_quantities["negative"]) == Decimal("-1")  # No validation

        # Test invalid types
        with pytest.raises(TypeError, match="Invalid quantity value"):
            coerce_qty(None)
        with pytest.raises(TypeError, match="Invalid quantity value"):
            coerce_qty([])
        with pytest.raises(TypeError, match="Invalid quantity value"):
            coerce_qty({})

    def test_coerce_rate(self, sample_rates: dict[str, int | float | str | Decimal]) -> None:
        """Test rate coercion with various inputs."""
        assert coerce_rate(sample_rates["int"]) == Decimal("5")
        assert coerce_rate(sample_rates["float"]) == Decimal("5.5")
        assert coerce_rate(sample_rates["str"]) == Decimal("5.25")
        assert coerce_rate(sample_rates["decimal"]) == Decimal("5.75")
        assert coerce_rate(sample_rates["zero"]) == Decimal("0")
        assert coerce_rate(sample_rates["negative"]) == Decimal("-1")  # No validation

        # Test invalid types
        with pytest.raises(TypeError, match="Invalid rate value"):
            coerce_rate(None)
        with pytest.raises(TypeError, match="Invalid rate value"):
            coerce_rate([])
        with pytest.raises(TypeError, match="Invalid rate value"):
            coerce_rate({})
