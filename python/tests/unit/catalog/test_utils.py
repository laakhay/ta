"""Tests for catalog utility functions."""

from datetime import UTC, datetime
from decimal import Decimal

from laakhay.ta.catalog.utils import jsonify_value, to_epoch_seconds, to_float


class TestJsonifyValue:
    """Test jsonify_value function."""

    def test_jsonify_decimal(self):
        """Test converting Decimal to float."""
        value = Decimal("100.5")
        result = jsonify_value(value)
        assert isinstance(result, float)
        assert result == 100.5

    def test_jsonify_list(self):
        """Test converting list with Decimals."""
        value = [Decimal("100"), Decimal("200"), Decimal("300")]
        result = jsonify_value(value)
        assert result == [100.0, 200.0, 300.0]

    def test_jsonify_dict(self):
        """Test converting dict with Decimals."""
        value = {"price": Decimal("100.5"), "volume": Decimal("1000")}
        result = jsonify_value(value)
        assert result == {"price": 100.5, "volume": 1000.0}

    def test_jsonify_nested(self):
        """Test converting nested structures."""
        value = {
            "prices": [Decimal("100"), Decimal("200")],
            "meta": {"total": Decimal("300")},
        }
        result = jsonify_value(value)
        assert result == {"prices": [100.0, 200.0], "meta": {"total": 300.0}}

    def test_jsonify_primitives(self):
        """Test that primitives pass through unchanged."""
        assert jsonify_value(100) == 100
        assert jsonify_value(100.5) == 100.5
        assert jsonify_value("string") == "string"
        assert jsonify_value(True) is True


class TestToEpochSeconds:
    """Test to_epoch_seconds function."""

    def test_to_epoch_seconds_datetime(self):
        """Test converting datetime to epoch seconds."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = to_epoch_seconds(dt)
        assert isinstance(result, int)
        assert result == int(dt.timestamp())

    def test_to_epoch_seconds_int(self):
        """Test converting int to epoch seconds."""
        result = to_epoch_seconds(1704110400)
        assert result == 1704110400

    def test_to_epoch_seconds_float(self):
        """Test converting float to epoch seconds."""
        result = to_epoch_seconds(1704110400.5)
        assert result == 1704110400

    def test_to_epoch_seconds_none(self):
        """Test converting None returns None."""
        assert to_epoch_seconds(None) is None

    def test_to_epoch_seconds_invalid(self):
        """Test converting invalid type returns None."""
        assert to_epoch_seconds("invalid") is None


class TestToFloat:
    """Test to_float function."""

    def test_to_float_decimal(self):
        """Test converting Decimal to float."""
        value = Decimal("100.5")
        result = to_float(value)
        assert isinstance(result, float)
        assert result == 100.5

    def test_to_float_int(self):
        """Test converting int to float."""
        assert to_float(100) == 100.0

    def test_to_float_float(self):
        """Test converting float to float."""
        assert to_float(100.5) == 100.5

    def test_to_float_bool(self):
        """Test converting bool to float."""
        assert to_float(True) == 1.0
        assert to_float(False) == 0.0

    def test_to_float_none(self):
        """Test converting None returns None."""
        assert to_float(None) is None

    def test_to_float_nan(self):
        """Test converting NaN returns None."""
        import math

        assert to_float(float("nan")) is None
        assert to_float(math.nan) is None

    def test_to_float_infinity(self):
        """Test converting infinity returns None."""
        import math

        assert to_float(float("inf")) is None
        assert to_float(math.inf) is None
        assert to_float(float("-inf")) is None

    def test_to_float_string(self):
        """Test converting string to float."""
        assert to_float("100.5") == 100.5
        assert to_float("100") == 100.0

    def test_to_float_invalid_string(self):
        """Test converting invalid string returns None."""
        assert to_float("invalid") is None
