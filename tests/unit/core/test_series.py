"""Consolidated Series tests - lean and efficient."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price


class TestSeriesCore:
    """Core Series functionality."""
    
    def test_creation(self, timestamp):
        """Test Series creation."""
        series = Series(
            timestamps=(timestamp,),
            values=(Price(Decimal("100")),),
            symbol="TEST",
            timeframe="1s"
        )
        assert len(series) == 1
        assert series.values[0] == Price(Decimal("100"))
    
    def test_empty_creation(self):
        """Test empty Series creation."""
        series = Series((), (), "TEST", "1s")
        assert len(series) == 0
    
    def test_validation_errors(self, timestamp):
        """Test Series validation errors."""
        with pytest.raises(ValueError, match="Timestamps and values must have the same length"):
            Series(
                timestamps=(timestamp,),
                values=(),
                symbol="TEST",
                timeframe="1s"
            )
    
    def test_indexing(self, price_series):
        """Test Series indexing."""
        assert price_series[0] == (price_series.timestamps[0], price_series.values[0])
    
    def test_iteration(self, multi_point_series):
        """Test Series iteration."""
        values = list(multi_point_series)
        assert len(values) == 2
        assert values[0] == (multi_point_series.timestamps[0], multi_point_series.values[0])
        assert values[1] == (multi_point_series.timestamps[1], multi_point_series.values[1])
    
    def test_time_slicing(self, multi_point_series):
        """Test Series time slicing."""
        # Test basic slicing
        sliced = multi_point_series[0:1]
        assert len(sliced) == 1


class TestSeriesOperations:
    """Series arithmetic operations - comprehensive coverage."""
    
    def test_addition_concatenation(self, price_series, timestamp):
        """Test Series addition with concatenation."""
        timestamp2 = datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
        series2 = Series(
            timestamps=(timestamp2,),
            values=(Price(Decimal("200")),),
            symbol="TEST",
            timeframe="1s"
        )
        result = price_series + series2
        assert len(result) == 2
    
    def test_addition_element_wise(self, multi_point_series, different_series):
        """Test Series addition element-wise."""
        result = multi_point_series + different_series
        assert len(result) == 2
        assert result.values[0] == Price(Decimal("150"))  # 100 + 50
        assert result.values[1] == Price(Decimal("275"))  # 200 + 75
    
    def test_addition_scalar(self, price_series):
        """Test Series addition with scalar."""
        result = price_series + 25
        assert result.values[0] == Price(Decimal("125"))  # 100 + 25
    
    def test_addition_validation_error(self, timestamp):
        """Test Series addition validation error."""
        series1 = Series((timestamp,), (Price(Decimal("100")),), "TEST1", "1s")
        series2 = Series((timestamp,), (Price(Decimal("200")),), "TEST2", "1s")
        with pytest.raises(ValueError, match="Cannot add series with different symbols"):
            series1 + series2
    
    def test_subtraction_element_wise(self, multi_point_series, different_series):
        """Test Series subtraction element-wise."""
        result = multi_point_series - different_series
        assert result.values[0] == Price(Decimal("50"))   # 100 - 50
        assert result.values[1] == Price(Decimal("125"))  # 200 - 75
    
    def test_subtraction_scalar(self, price_series):
        """Test Series subtraction with scalar."""
        result = price_series - 25
        assert result.values[0] == Price(Decimal("75"))  # 100 - 25
    
    def test_subtraction_different_lengths_error(self, multi_point_series, price_series):
        """Test Series subtraction with different lengths."""
        with pytest.raises(ValueError, match="Cannot subtract series of different lengths"):
            multi_point_series - price_series
    
    def test_subtraction_type_error(self, timestamp):
        """Test Series subtraction type error."""
        series1 = Series((timestamp,), (Price(Decimal("100")),), "TEST", "1s")
        series2 = Series((timestamp,), ("invalid",), "TEST", "1s")
        with pytest.raises(TypeError, match="Cannot subtract series values of types"):
            series1 - series2
    
    def test_subtraction_scalar_type_error(self, price_series):
        """Test Series subtraction scalar type error."""
        with pytest.raises(TypeError, match="Cannot subtract <class 'str'> from series values"):
            price_series - "invalid"
    
    def test_multiplication_element_wise(self, multi_point_series, different_series):
        """Test Series multiplication element-wise."""
        result = multi_point_series * different_series
        assert result.values[0] == Price(Decimal("5000"))   # 100 * 50
        assert result.values[1] == Price(Decimal("15000"))  # 200 * 75
    
    def test_multiplication_scalar(self, price_series):
        """Test Series multiplication with scalar."""
        result = price_series * Decimal("2.5")
        assert result.values[0] == Price(Decimal("250"))  # 100 * 2.5
    
    def test_multiplication_different_lengths_error(self, multi_point_series, price_series):
        """Test Series multiplication with different lengths."""
        with pytest.raises(ValueError, match="Cannot multiply series of different lengths"):
            multi_point_series * price_series
    
    def test_multiplication_type_error(self, timestamp):
        """Test Series multiplication type error."""
        series1 = Series((timestamp,), (Price(Decimal("100")),), "TEST", "1s")
        series2 = Series((timestamp,), ("invalid",), "TEST", "1s")
        with pytest.raises(TypeError, match="Cannot multiply series values of types"):
            series1 * series2
    
    def test_multiplication_scalar_type_error(self, price_series):
        """Test Series multiplication scalar type error."""
        with pytest.raises(TypeError, match="Cannot multiply series values of type"):
            price_series * "invalid"
    
    def test_division_element_wise(self, multi_point_series, different_series):
        """Test Series division element-wise."""
        result = multi_point_series / different_series
        assert result.values[0] == Price(Decimal("2"))     # 100 / 50
        assert result.values[1] == Price(Decimal("2.666666666666666666666666667"))  # 200 / 75
    
    def test_division_scalar(self, price_series):
        """Test Series division with scalar."""
        result = price_series / 4
        assert result.values[0] == Price(Decimal("25"))  # 100 / 4
    
    def test_division_different_lengths_error(self, multi_point_series, price_series):
        """Test Series division with different lengths."""
        with pytest.raises(ValueError, match="Cannot divide series of different lengths"):
            multi_point_series / price_series
    
    def test_division_type_error(self, timestamp):
        """Test Series division type error."""
        series1 = Series((timestamp,), (Price(Decimal("100")),), "TEST", "1s")
        series2 = Series((timestamp,), ("invalid",), "TEST", "1s")
        with pytest.raises(TypeError, match="Cannot divide series values of types"):
            series1 / series2
    
    def test_division_scalar_zero_division_error(self, price_series):
        """Test Series division by zero."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            price_series / 0
    
    def test_modulo_element_wise(self, multi_point_series, different_series):
        """Test Series modulo element-wise."""
        result = multi_point_series % different_series
        assert result.values[0] == Price(Decimal("0"))   # 100 % 50 = 0
        assert result.values[1] == Price(Decimal("50"))  # 200 % 75 = 50
    
    def test_modulo_scalar(self, price_series):
        """Test Series modulo with scalar."""
        result = price_series % 7
        assert result.values[0] == Price(Decimal("2"))  # 100 % 7 = 2
    
    def test_modulo_different_lengths_error(self, multi_point_series, price_series):
        """Test Series modulo with different lengths."""
        with pytest.raises(ValueError, match="Cannot perform modulo on series of different lengths"):
            multi_point_series % price_series
    
    def test_modulo_type_error(self, timestamp):
        """Test Series modulo type error."""
        series1 = Series((timestamp,), (Price(Decimal("100")),), "TEST", "1s")
        series2 = Series((timestamp,), ("invalid",), "TEST", "1s")
        with pytest.raises(TypeError, match="Cannot perform modulo on series values of types"):
            series1 % series2
    
    def test_modulo_scalar_zero_division_error(self, price_series):
        """Test Series modulo by zero."""
        with pytest.raises(ZeroDivisionError, match="Cannot perform modulo with zero in series"):
            price_series % 0
    
    def test_power_element_wise(self, multi_point_series, different_series):
        """Test Series power element-wise."""
        result = multi_point_series ** different_series
        assert result.values[0] == Price(Decimal("1.000000000000000000000000000E+100"))  # 100^50
        assert result.values[1] == Price(Decimal("3.777893186295716170956800000E+172"))  # 200^75
    
    def test_power_scalar(self, price_series):
        """Test Series power with scalar."""
        result = price_series ** 3
        assert result.values[0] == Price(Decimal("1000000"))  # 100^3
    
    def test_power_different_lengths_error(self, multi_point_series, price_series):
        """Test Series power with different lengths."""
        with pytest.raises(ValueError, match="Cannot perform power on series of different lengths"):
            multi_point_series ** price_series
    
    def test_power_type_error(self, timestamp):
        """Test Series power type error."""
        series1 = Series((timestamp,), (Price(Decimal("100")),), "TEST", "1s")
        series2 = Series((timestamp,), ("invalid",), "TEST", "1s")
        with pytest.raises(TypeError, match="Cannot perform power on series values of types"):
            series1 ** series2
    
    def test_power_scalar_type_error(self, price_series):
        """Test Series power scalar type error."""
        with pytest.raises(TypeError, match="Cannot perform power on series values of type"):
            price_series ** "invalid"


class TestSeriesUnaryOperations:
    """Series unary operations."""
    
    def test_negation(self, price_series):
        """Test Series negation."""
        result = -price_series
        assert result.values[0] == Price(Decimal("-100"))
    
    def test_negation_type_error(self, timestamp):
        """Test Series negation type error."""
        series = Series((timestamp,), ("invalid",), "TEST", "1s")
        with pytest.raises(TypeError, match="Cannot negate series values of type"):
            -series
    
    def test_positive(self, price_series):
        """Test Series positive operation."""
        result = +price_series
        assert result.values[0] == Price(Decimal("100"))
    
    def test_positive_negative_value(self, timestamp):
        """Test Series positive with negative value."""
        series = Series((timestamp,), (Price(Decimal("-100")),), "TEST", "1s")
        result = +series
        assert result.values[0] == Price(Decimal("-100"))


class TestSeriesSerialization:
    """Series serialization."""
    
    def test_serialization(self, price_series):
        """Test Series serialization."""
        data = price_series.to_dict()
        assert data["symbol"] == "TEST"
        assert data["timeframe"] == "1s"
        assert len(data["timestamps"]) == 1
        assert len(data["values"]) == 1
        
        restored = Series.from_dict(data)
        assert restored == price_series


class TestSeriesTypes:
    """Series type aliases."""
    
    def test_type_aliases(self):
        """Test Series type aliases."""
        from laakhay.ta.core.series import PriceSeries, QtySeries
        assert PriceSeries is not None
        assert QtySeries is not None
