"""Tests for relative strength analysis."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from laakhay.ta.analytics.relative_strength import RelativeStrengthAnalyzer
from laakhay.ta.models import Candle


def create_test_candle(
    timestamp: datetime,
    close: float,
    symbol: str = "BTCUSDT",
) -> Candle:
    """Helper to create test candles."""
    return Candle(
        symbol=symbol,
        timestamp=timestamp,
        open=Decimal(str(close)),
        high=Decimal(str(close * 1.01)),
        low=Decimal(str(close * 0.99)),
        close=Decimal(str(close)),
        volume=Decimal("1000"),
    )


class TestRelativeStrengthCalculation:
    """Test relative strength calculation."""

    def test_symbol_outperforming(self):
        """Test symbol outperforming base."""
        # Symbol: 3000 -> 3200 (+6.67%)
        # Base: 90000 -> 91800 (+2%)
        # RS: 6.67 - 2 = 4.67%
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("3200"),
            base_start_price=Decimal("90000"),
            base_current_price=Decimal("91800"),
            timestamp=ts,
        )

        assert rs.is_outperforming is True
        assert float(rs.relative_strength) > 4.5
        assert float(rs.symbol_change_pct) > 6.5
        assert float(rs.base_change_pct) < 2.1
        assert rs.strength_category == "moderate_out"

    def test_symbol_underperforming(self):
        """Test symbol underperforming base."""
        # Symbol: 3000 -> 2900 (-3.33%)
        # Base: 90000 -> 91800 (+2%)
        # RS: -3.33 - 2 = -5.33%
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("2900"),
            base_start_price=Decimal("90000"),
            base_current_price=Decimal("91800"),
            timestamp=ts,
        )

        assert rs.is_outperforming is False
        assert float(rs.relative_strength) < -5
        assert rs.strength_category == "strong_under"

    def test_neutral_performance(self):
        """Test neutral relative performance."""
        # Symbol: 3000 -> 3060 (+2%)
        # Base: 90000 -> 91800 (+2%)
        # RS: 2 - 2 = 0%
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("3060"),
            base_start_price=Decimal("90000"),
            base_current_price=Decimal("91800"),
            timestamp=ts,
        )

        assert abs(float(rs.relative_strength)) < 0.1
        assert rs.strength_category == "neutral"

    def test_strength_categories(self):
        """Test strength category classification."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        base_start = Decimal("90000")
        base_current = Decimal("90000")  # 0% change

        # Strong outperformance (+6%)
        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("3180"),
            base_start_price=base_start,
            base_current_price=base_current,
            timestamp=ts,
        )
        assert rs.strength_category == "strong_out"

        # Moderate outperformance (+3%)
        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("3090"),
            base_start_price=base_start,
            base_current_price=base_current,
            timestamp=ts,
        )
        assert rs.strength_category == "moderate_out"

        # Strong underperformance (-6%)
        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("2820"),
            base_start_price=base_start,
            base_current_price=base_current,
            timestamp=ts,
        )
        assert rs.strength_category == "strong_under"


class TestDivergenceDetection:
    """Test divergence detection."""

    def test_bullish_divergence(self):
        """Test bullish divergence detection."""
        # Symbol up +5%, base flat
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("3150"),  # +5%
            base_start_price=Decimal("90000"),
            base_current_price=Decimal("90000"),  # 0%
            timestamp=ts,
            divergence_threshold=Decimal("2.0"),
        )

        assert rs.divergence_type == "bullish"

    def test_bearish_divergence(self):
        """Test bearish divergence detection."""
        # Symbol down -5%, base flat
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("2850"),  # -5%
            base_start_price=Decimal("90000"),
            base_current_price=Decimal("90000"),  # 0%
            timestamp=ts,
            divergence_threshold=Decimal("2.0"),
        )

        assert rs.divergence_type == "bearish"

    def test_no_divergence_both_up(self):
        """Test no divergence when both moving together."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

        rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            symbol_start_price=Decimal("3000"),
            symbol_current_price=Decimal("3150"),  # +5%
            base_start_price=Decimal("90000"),
            base_current_price=Decimal("92700"),  # +3%
            timestamp=ts,
            divergence_threshold=Decimal("2.0"),
        )

        assert rs.divergence_type == "none"


class TestRelativeStrengthSeries:
    """Test relative strength series calculation."""

    def test_series_calculation(self):
        """Test series-first calculation."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Create symbol going up 10% over 10 periods
        symbol_candles = [
            create_test_candle(base_time + timedelta(hours=i), 3000 + i * 30, symbol="ETHUSDT")
            for i in range(10)
        ]

        # Create base going up 5% over 10 periods
        base_candles = [
            create_test_candle(base_time + timedelta(hours=i), 90000 + i * 500, symbol="BTCUSDT")
            for i in range(10)
        ]

        results = RelativeStrengthAnalyzer.calculate_relative_strength_series(
            symbol_candles, base_candles, reference_index=0
        )

        # Should have 9 results (10 candles - 1 reference)
        assert len(results) == 9

        # All should show outperformance (symbol rising faster)
        for rs in results:
            assert rs.is_outperforming is True

        # Relative strength should increase over time
        assert results[-1].relative_strength > results[0].relative_strength

    def test_series_with_different_reference(self):
        """Test series with non-zero reference index."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        symbol_candles = [
            create_test_candle(base_time + timedelta(hours=i), 3000 + i * 30, symbol="ETHUSDT")
            for i in range(10)
        ]
        base_candles = [
            create_test_candle(base_time + timedelta(hours=i), 90000 + i * 500, symbol="BTCUSDT")
            for i in range(10)
        ]

        # Use index 5 as reference
        results = RelativeStrengthAnalyzer.calculate_relative_strength_series(
            symbol_candles, base_candles, reference_index=5
        )

        # Should have 4 results (10 candles - 5 reference - 1)
        assert len(results) == 4

    def test_insufficient_data_raises(self):
        """Test that insufficient data raises ValueError."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        symbol_candles = [create_test_candle(base_time, 3000, symbol="ETHUSDT")]
        base_candles = [create_test_candle(base_time, 90000, symbol="BTCUSDT")]

        try:
            RelativeStrengthAnalyzer.calculate_relative_strength_series(
                symbol_candles, base_candles
            )
            raise AssertionError("Should raise ValueError")
        except ValueError as e:
            assert "at least 2" in str(e)


class TestRanking:
    """Test ranking by relative strength."""

    def test_rank_multiple_symbols(self):
        """Test ranking multiple symbols by RS."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Create base asset (BTC)
        base_candles = [
            create_test_candle(base_time + timedelta(hours=i), 90000 + i * 100, symbol="BTCUSDT")
            for i in range(10)
        ]

        # Create multiple symbols with different performance
        symbols = {
            "ETHUSDT": [  # Strong performer (+10%)
                create_test_candle(base_time + timedelta(hours=i), 3000 + i * 30, symbol="ETHUSDT")
                for i in range(10)
            ],
            "SOLUSDT": [  # Moderate performer (+5%)
                create_test_candle(base_time + timedelta(hours=i), 100 + i * 0.5, symbol="SOLUSDT")
                for i in range(10)
            ],
            "BNBUSDT": [  # Underperformer (-2%)
                create_test_candle(base_time + timedelta(hours=i), 500 - i * 1, symbol="BNBUSDT")
                for i in range(10)
            ],
        }

        rankings = RelativeStrengthAnalyzer.rank_by_relative_strength(
            symbols, base_candles, reference_index=0
        )

        assert len(rankings) == 3

        # Should be sorted by RS (descending)
        assert rankings[0][0] == "ETHUSDT"  # Best performer
        assert rankings[1][0] == "SOLUSDT"  # Middle
        assert rankings[2][0] == "BNBUSDT"  # Worst performer

        # Check RS values are in correct order
        assert rankings[0][1].relative_strength > rankings[1][1].relative_strength
        assert rankings[1][1].relative_strength > rankings[2][1].relative_strength

    def test_rank_with_top_n(self):
        """Test ranking with top_n limit."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        base_candles = [
            create_test_candle(base_time + timedelta(hours=j), 90000 + j * 100, symbol="BTCUSDT")
            for j in range(10)
        ]

        symbols = {
            f"SYM{i}": [
                create_test_candle(base_time + timedelta(hours=j), 100 + i * j, symbol=f"SYM{i}")
                for j in range(10)
            ]
            for i in range(5)
        }

        rankings = RelativeStrengthAnalyzer.rank_by_relative_strength(
            symbols, base_candles, reference_index=0, top_n=3
        )

        # Should return only top 3
        assert len(rankings) == 3

    def test_rank_skips_insufficient_data(self):
        """Test ranking skips symbols with insufficient data."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        base_candles = [
            create_test_candle(base_time + timedelta(hours=i), 90000 + i * 100, symbol="BTCUSDT")
            for i in range(10)
        ]

        symbols = {
            "GOOD": [
                create_test_candle(base_time + timedelta(hours=i), 100 + i * 1, symbol="GOOD")
                for i in range(10)
            ],
            "BAD": [create_test_candle(base_time, 100, symbol="BAD")],  # Only 1 candle
        }

        rankings = RelativeStrengthAnalyzer.rank_by_relative_strength(
            symbols, base_candles, reference_index=0
        )

        # Should only have GOOD symbol
        assert len(rankings) == 1
        assert rankings[0][0] == "GOOD"
