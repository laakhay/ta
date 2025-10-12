"""Tests for statistical utilities module."""

from decimal import Decimal
from math import log

import pytest

from laakhay.ta.analytics.statistics import StatisticalUtils


class TestReturnsCalculation:
    """Test returns calculation methods."""

    def test_log_returns(self):
        """Test log returns calculation."""
        prices = [Decimal("100"), Decimal("105"), Decimal("110")]

        returns = StatisticalUtils.calculate_returns(prices, method="log")

        assert len(returns) == 2
        # log(105/100) ≈ 0.0488
        assert abs(returns[0] - log(105/100)) < 0.0001
        # log(110/105) ≈ 0.0465
        assert abs(returns[1] - log(110/105)) < 0.0001

    def test_pct_returns(self):
        """Test percentage returns calculation."""
        prices = [Decimal("100"), Decimal("105"), Decimal("110")]

        returns = StatisticalUtils.calculate_returns(prices, method="pct")

        assert len(returns) == 2
        # (105-100)/100 = 0.05
        assert abs(returns[0] - 0.05) < 0.0001
        # (110-105)/105 ≈ 0.0476
        assert abs(returns[1] - (5/105)) < 0.0001

    def test_simple_returns(self):
        """Test simple returns calculation."""
        prices = [Decimal("100"), Decimal("105"), Decimal("110")]

        returns = StatisticalUtils.calculate_returns(prices, method="simple")

        assert len(returns) == 2
        assert returns[0] == 5.0  # 105 - 100
        assert returns[1] == 5.0  # 110 - 105

    def test_returns_insufficient_data(self):
        """Test error handling for insufficient data."""
        prices = [Decimal("100")]

        with pytest.raises(ValueError, match="Need at least 2 prices"):
            StatisticalUtils.calculate_returns(prices)

    def test_returns_invalid_method(self):
        """Test error handling for invalid method."""
        prices = [Decimal("100"), Decimal("105")]

        with pytest.raises(ValueError, match="Invalid method"):
            StatisticalUtils.calculate_returns(prices, method="invalid")  # type: ignore

    def test_returns_negative_values(self):
        """Test returns with declining prices."""
        prices = [Decimal("110"), Decimal("105"), Decimal("100")]

        log_returns = StatisticalUtils.calculate_returns(prices, method="log")
        pct_returns = StatisticalUtils.calculate_returns(prices, method="pct")

        # All returns should be negative
        assert all(r < 0 for r in log_returns)
        assert all(r < 0 for r in pct_returns)


class TestPercentileRank:
    """Test percentile rank calculation."""

    def test_percentile_median_value(self):
        """Test percentile for median value."""
        values = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]

        percentile = StatisticalUtils.percentile_rank(102.5, values)

        # Above 3 of 6 values = 50%
        assert abs(percentile - 50.0) < 1.0

    def test_percentile_extreme_values(self):
        """Test percentile for extreme values."""
        values = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]

        # Very high value
        high_percentile = StatisticalUtils.percentile_rank(110.0, values)
        assert high_percentile == 100.0

        # Very low value
        low_percentile = StatisticalUtils.percentile_rank(90.0, values)
        assert low_percentile == 0.0

    def test_percentile_exact_match(self):
        """Test percentile for exact match in values."""
        values = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]

        # Exact match at 103 - above 3 of 6 values
        percentile = StatisticalUtils.percentile_rank(103.0, values)
        assert percentile == 50.0

    def test_percentile_empty_values(self):
        """Test percentile with empty values."""
        percentile = StatisticalUtils.percentile_rank(100.0, [])
        assert percentile == 0.0


class TestZScore:
    """Test z-score calculation."""

    def test_zscore_at_mean(self):
        """Test z-score for value at mean."""
        values = [100.0, 102.0, 104.0, 106.0, 108.0]
        mean_value = sum(values) / len(values)  # 104.0

        zscore = StatisticalUtils.zscore(mean_value, values)

        # Value at mean should have z-score close to 0
        assert abs(zscore) < 0.1

    def test_zscore_above_mean(self):
        """Test z-score for value above mean."""
        values = [100.0, 102.0, 104.0, 106.0, 108.0]

        # Value well above mean
        zscore = StatisticalUtils.zscore(120.0, values)

        assert zscore > 3  # More than 3 std devs above mean

    def test_zscore_below_mean(self):
        """Test z-score for value below mean."""
        values = [100.0, 102.0, 104.0, 106.0, 108.0]

        # Value well below mean
        zscore = StatisticalUtils.zscore(80.0, values)

        assert zscore < -3  # More than 3 std devs below mean

    def test_zscore_zero_std(self):
        """Test z-score when std is zero (all values same)."""
        values = [100.0, 100.0, 100.0, 100.0, 100.0]

        zscore = StatisticalUtils.zscore(105.0, values)

        # Zero std should return 0
        assert zscore == 0.0

    def test_zscore_insufficient_data(self):
        """Test z-score with insufficient data."""
        # Single value
        zscore = StatisticalUtils.zscore(100.0, [100.0])
        assert zscore == 0.0

        # Empty list
        zscore = StatisticalUtils.zscore(100.0, [])
        assert zscore == 0.0


class TestVolatility:
    """Test volatility calculation."""

    def test_volatility_basic(self):
        """Test basic volatility calculation."""
        returns = [0.01, -0.01, 0.02, -0.02, 0.015]

        vol = StatisticalUtils.calculate_volatility(returns)

        assert vol > 0
        # Volatility should be reasonable for the given returns
        assert 0.01 < vol < 0.1

    def test_volatility_annualized(self):
        """Test annualized volatility."""
        returns = [0.01, -0.01, 0.02, -0.02, 0.015]

        daily_vol = StatisticalUtils.calculate_volatility(returns, annualization_factor=1)
        annual_vol = StatisticalUtils.calculate_volatility(returns, annualization_factor=252)

        # Annualized should be higher
        assert annual_vol > daily_vol
        # Should be approximately sqrt(252) times higher
        assert abs(annual_vol / daily_vol - (252 ** 0.5)) < 0.1

    def test_volatility_zero_returns(self):
        """Test volatility with zero returns."""
        returns = [0.0, 0.0, 0.0, 0.0, 0.0]

        vol = StatisticalUtils.calculate_volatility(returns)

        # Zero returns should have zero volatility
        assert vol == 0.0

    def test_volatility_insufficient_data(self):
        """Test volatility with insufficient data."""
        # Single return
        vol = StatisticalUtils.calculate_volatility([0.01])
        assert vol == 0.0

        # Empty list
        vol = StatisticalUtils.calculate_volatility([])
        assert vol == 0.0


class TestSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_sharpe_positive_returns(self):
        """Test Sharpe ratio with positive returns."""
        returns = [0.01, 0.02, 0.015, 0.008, 0.012]

        sharpe = StatisticalUtils.calculate_sharpe_ratio(returns, risk_free_rate=0.001)

        # Positive excess returns should give positive Sharpe
        assert sharpe > 0

    def test_sharpe_negative_returns(self):
        """Test Sharpe ratio with negative returns."""
        returns = [-0.01, -0.02, -0.015, -0.008, -0.012]

        sharpe = StatisticalUtils.calculate_sharpe_ratio(returns, risk_free_rate=0.001)

        # Negative excess returns should give negative Sharpe
        assert sharpe < 0

    def test_sharpe_annualized(self):
        """Test annualized Sharpe ratio."""
        returns = [0.01, 0.02, 0.015, 0.008, 0.012]

        daily_sharpe = StatisticalUtils.calculate_sharpe_ratio(
            returns, risk_free_rate=0.001, annualization_factor=1
        )
        annual_sharpe = StatisticalUtils.calculate_sharpe_ratio(
            returns, risk_free_rate=0.001, annualization_factor=252
        )

        # Annualized should be higher
        assert annual_sharpe > daily_sharpe
        # Should be approximately sqrt(252) times higher
        assert abs(annual_sharpe / daily_sharpe - (252 ** 0.5)) < 0.1

    def test_sharpe_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        returns = [0.01, 0.01, 0.01, 0.01, 0.01]

        sharpe = StatisticalUtils.calculate_sharpe_ratio(returns, risk_free_rate=0.001)

        # Zero std should return 0
        assert sharpe == 0.0

    def test_sharpe_insufficient_data(self):
        """Test Sharpe ratio with insufficient data."""
        # Single return
        sharpe = StatisticalUtils.calculate_sharpe_ratio([0.01])
        assert sharpe == 0.0

        # Empty list
        sharpe = StatisticalUtils.calculate_sharpe_ratio([])
        assert sharpe == 0.0

    def test_sharpe_with_risk_free_rate(self):
        """Test Sharpe ratio accounts for risk-free rate correctly."""
        returns = [0.01, 0.02, 0.015, 0.008, 0.012]

        sharpe_no_rf = StatisticalUtils.calculate_sharpe_ratio(returns, risk_free_rate=0.0)
        sharpe_with_rf = StatisticalUtils.calculate_sharpe_ratio(returns, risk_free_rate=0.005)

        # Higher risk-free rate should reduce Sharpe ratio
        assert sharpe_with_rf < sharpe_no_rf
