"""Tests for correlation analysis."""

from datetime import datetime, timezone
from decimal import Decimal

from laakhay.ta.analytics.correlation import CorrelationAnalyzer
from laakhay.ta.models import Candle


def create_test_candle(
    timestamp: datetime, close: float, open_: float = None, symbol: str = "BTCUSDT"
) -> Candle:
    """Helper to create test candles."""
    if open_ is None:
        open_ = close
    return Candle(
        symbol=symbol,
        timestamp=timestamp,
        open=Decimal(str(open_)),
        high=Decimal(str(close * 1.01)),
        low=Decimal(str(close * 0.99)),
        close=Decimal(str(close)),
        volume=Decimal("1000"),
    )


class TestPearsonCorrelation:
    """Test pure Pearson correlation calculation."""

    def test_perfect_positive_correlation(self):
        """Test perfect positive correlation (r = 1.0)."""
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [2.0, 4.0, 6.0, 8.0, 10.0]

        corr = CorrelationAnalyzer.calculate_pearson_correlation(
            series1, series2
        )

        assert abs(corr - 1.0) < 0.0001, "Perfect positive correlation"

    def test_perfect_negative_correlation(self):
        """Test perfect negative correlation (r = -1.0)."""
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [10.0, 8.0, 6.0, 4.0, 2.0]

        corr = CorrelationAnalyzer.calculate_pearson_correlation(
            series1, series2
        )

        assert abs(corr - (-1.0)) < 0.0001, "Perfect negative correlation"

    def test_zero_correlation(self):
        """Test uncorrelated series (r ≈ 0)."""
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [3.0, 1.0, 4.0, 2.0, 5.0]

        corr = CorrelationAnalyzer.calculate_pearson_correlation(
            series1, series2
        )

        # Should be close to 0 but not exactly due to small sample
        assert abs(corr) < 0.9, "Near-zero correlation"

    def test_mismatched_lengths_raises(self):
        """Test that mismatched series lengths raise ValueError."""
        series1 = [1.0, 2.0, 3.0]
        series2 = [1.0, 2.0]

        try:
            CorrelationAnalyzer.calculate_pearson_correlation(
                series1, series2
            )
            raise AssertionError("Should raise ValueError")
        except ValueError as e:
            assert "same length" in str(e)

    def test_insufficient_data_raises(self):
        """Test that single data point raises ValueError."""
        series1 = [1.0]
        series2 = [2.0]

        try:
            CorrelationAnalyzer.calculate_pearson_correlation(
                series1, series2
            )
            raise AssertionError("Should raise ValueError")
        except ValueError as e:
            assert "at least 2" in str(e)

    def test_constant_series_returns_zero(self):
        """Test that constant series returns 0 correlation."""
        series1 = [5.0, 5.0, 5.0, 5.0]
        series2 = [1.0, 2.0, 3.0, 4.0]

        corr = CorrelationAnalyzer.calculate_pearson_correlation(
            series1, series2
        )

        assert corr == 0.0, "Constant series has no correlation"


class TestCandleSeriesCorrelation:
    """Test correlation between candle series."""

    def test_correlated_candle_series(self):
        """Test correlation calculation from candle series."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles1 = [
            create_test_candle(base_time, 100 + i * 2) for i in range(10)
        ]
        candles2 = [
            create_test_candle(base_time, 50 + i) for i in range(10)
        ]

        result = CorrelationAnalyzer.correlate_candle_series(
            candles1,
            candles2,
            asset1_name="BTC",
            asset2_name="ETH",
        )

        assert result.asset1 == "BTC"
        assert result.asset2 == "ETH"
        assert result.correlation > 0.95, "Should be highly correlated"
        assert result.lookback_periods == 10
        assert result.data_points == 10

    def test_different_price_fields(self):
        """Test correlation using different price fields."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles1 = [
            Candle(
                symbol="BTCUSDT",
                timestamp=base_time,
                open=Decimal("100"),
                high=Decimal("105"),
                low=Decimal("95"),
                close=Decimal("102"),
                volume=Decimal("1000"),
            )
            for i in range(5)
        ]
        candles2 = [
            Candle(
                symbol="ETHUSDT",
                timestamp=base_time,
                open=Decimal("50"),
                high=Decimal("52"),
                low=Decimal("48"),
                close=Decimal("51"),
                volume=Decimal("1000"),
            )
            for i in range(5)
        ]

        result_close = CorrelationAnalyzer.correlate_candle_series(
            candles1, candles2, price_field="close"
        )
        result_open = CorrelationAnalyzer.correlate_candle_series(
            candles1, candles2, price_field="open"
        )

        # Both should work (though correlation will be undefined for constant series)
        assert result_close.correlation == 0.0  # Constant series
        assert result_open.correlation == 0.0  # Constant series


class TestCorrelationDetection:
    """Test correlation change detection."""

    def test_significant_correlation_detected(self):
        """Test detection of significant correlation."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # Create highly correlated series
        candles1 = [
            create_test_candle(base_time, 100 + i * 5) for i in range(20)
        ]
        candles2 = [
            create_test_candle(base_time, 50 + i * 2.5) for i in range(20)
        ]

        result = CorrelationAnalyzer.detect_correlation_change(
            candles1, candles2, significance_threshold=0.7
        )

        assert result.is_significant is True
        assert result.strength == "strong"
        assert result.correlation > 0.95

    def test_weak_correlation_not_significant(self):
        """Test that weak correlation is not marked significant."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # Create weakly correlated series
        candles1 = [create_test_candle(base_time, 100 + i) for i in range(20)]
        candles2 = [
            create_test_candle(base_time, 50 + (i % 3)) for i in range(20)
        ]

        result = CorrelationAnalyzer.detect_correlation_change(
            candles1, candles2, significance_threshold=0.7
        )

        assert result.is_significant is False
        assert result.strength in ["weak", "moderate"]

    def test_strength_classification(self):
        """Test correlation strength classification."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Strong correlation (> 0.7)
        candles1 = [
            create_test_candle(base_time, 100 + i * 5) for i in range(20)
        ]
        candles2 = [
            create_test_candle(base_time, 50 + i * 2.5) for i in range(20)
        ]

        result = CorrelationAnalyzer.detect_correlation_change(
            candles1, candles2
        )
        assert result.strength == "strong"


class TestRollingCorrelation:
    """Test rolling correlation series."""

    def test_rolling_correlation_series(self):
        """Test rolling correlation over time."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # Create 50 candles
        candles1 = [
            create_test_candle(base_time, 100 + i) for i in range(50)
        ]
        candles2 = [create_test_candle(base_time, 50 + i) for i in range(50)]

        results = CorrelationAnalyzer.rolling_correlation_series(
            candles1, candles2, window_size=10
        )

        # Should get 50 - 10 + 1 = 41 results
        assert len(results) == 41
        # All should be highly correlated
        for r in results:
            assert r.correlation > 0.95
            assert r.lookback_periods == 10

    def test_rolling_correlation_minimum_window(self):
        """Test rolling correlation with minimum window size."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles1 = [create_test_candle(base_time, 100 + i) for i in range(10)]
        candles2 = [create_test_candle(base_time, 50 + i) for i in range(10)]

        results = CorrelationAnalyzer.rolling_correlation_series(
            candles1, candles2, window_size=5
        )

        # Should get 10 - 5 + 1 = 6 results
        assert len(results) == 6

    def test_insufficient_data_raises(self):
        """Test that insufficient data raises ValueError."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        candles1 = [create_test_candle(base_time, 100 + i) for i in range(5)]
        candles2 = [create_test_candle(base_time, 50 + i) for i in range(5)]

        try:
            CorrelationAnalyzer.rolling_correlation_series(
                candles1, candles2, window_size=10
            )
            raise AssertionError("Should raise ValueError")
        except ValueError as e:
            assert "at least 10" in str(e)
