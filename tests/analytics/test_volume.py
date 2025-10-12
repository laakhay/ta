"""Tests for volume analysis module."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.analytics.volume import VolumeAnalyzer, VolumeWindowAnalysis
from laakhay.ta.models import Candle


def create_test_candle(timestamp: datetime, volume: Decimal, symbol: str = "TEST") -> Candle:
    """Helper to create test candles."""
    return Candle(
        symbol=symbol,
        timestamp=timestamp,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=volume,
    )


class TestVolumeStatistics:
    """Test volume statistics calculation."""

    def test_statistics_single_window(self):
        """Test calculating statistics for a single window."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(100 + i * 10)),  # Increasing volume
            )
            for i in range(50)
        ]

        stats = VolumeAnalyzer.calculate_volume_statistics(
            candles, windows={"test": 20}
        )

        assert "test" in stats
        assert not stats["test"]["insufficient_data"]
        assert stats["test"]["median"] > 0
        assert stats["test"]["mean"] > 0
        assert stats["test"]["std"] > 0
        assert stats["test"]["min"] > 0
        assert stats["test"]["max"] > 0

    def test_statistics_multiple_windows(self):
        """Test calculating statistics for multiple windows."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(1000 + i)),
            )
            for i in range(200)
        ]

        stats = VolumeAnalyzer.calculate_volume_statistics(
            candles, windows={"short": 20, "medium": 100}
        )

        assert "short" in stats
        assert "medium" in stats
        assert not stats["short"]["insufficient_data"]
        assert not stats["medium"]["insufficient_data"]

        # Short window should have higher median (more recent candles)
        assert stats["short"]["median"] > stats["medium"]["median"]

    def test_statistics_insufficient_data(self):
        """Test handling insufficient data for window."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal("1000"),
            )
            for i in range(10)
        ]

        stats = VolumeAnalyzer.calculate_volume_statistics(
            candles, windows={"large": 100}
        )

        assert stats["large"]["insufficient_data"]
        assert stats["large"]["median"] == Decimal("0")
        assert stats["large"]["mean"] == Decimal("0")

    def test_statistics_default_windows(self):
        """Test default windows (short=20, medium=100)."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal("1000"),
            )
            for i in range(150)
        ]

        stats = VolumeAnalyzer.calculate_volume_statistics(candles)

        assert "short" in stats
        assert "medium" in stats


class TestVolumeVsBaselines:
    """Test volume vs baselines analysis."""

    def test_analyze_above_baseline(self):
        """Test analyzing volume above baseline."""
        base_time = datetime(2024, 1, 1, 0, 0)
        # Varying volumes so std != 0
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(900 + i * 2)),  # Gradually increasing
            )
            for i in range(50)
        ]

        current_volume = Decimal("3000")  # Much higher than baseline

        results = VolumeAnalyzer.analyze_volume_vs_baselines(
            current_volume=current_volume,
            candles=candles,
            windows={"test": 20},
            baseline_method="median",
        )

        assert "test" in results
        result = results["test"]
        assert isinstance(result, VolumeWindowAnalysis)
        assert result.multiplier > Decimal("2")  # Should be well above baseline
        assert result.percentile > 95  # Should be in top percentile
        assert result.zscore > 2  # Should be multiple std devs above mean
        assert not result.insufficient_data

    def test_analyze_below_baseline(self):
        """Test analyzing volume below baseline."""
        base_time = datetime(2024, 1, 1, 0, 0)
        # Varying volumes so std != 0
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(900 + i * 4)),  # Increasing volumes
            )
            for i in range(50)
        ]

        current_volume = Decimal("500")  # Below baseline

        results = VolumeAnalyzer.analyze_volume_vs_baselines(
            current_volume=current_volume,
            candles=candles,
            windows={"test": 20},
        )

        result = results["test"]
        assert result.multiplier < Decimal("1")
        assert result.percentile < 50  # Below median
        assert result.zscore < 0  # Below mean

    def test_analyze_multiple_windows(self):
        """Test analyzing against multiple windows."""
        base_time = datetime(2024, 1, 1, 0, 0)
        # Increasing volume trend
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(500 + i * 10)),
            )
            for i in range(200)
        ]

        current_volume = Decimal("3000")

        results = VolumeAnalyzer.analyze_volume_vs_baselines(
            current_volume=current_volume,
            candles=candles,
            windows={"short": 20, "medium": 100, "long": 150},
        )

        assert len(results) == 3
        # With increasing trend, multiplier should be lower for short window
        assert results["short"].multiplier < results["long"].multiplier

    def test_analyze_median_vs_mean_baseline(self):
        """Test median vs mean baseline methods."""
        base_time = datetime(2024, 1, 1, 0, 0)
        # Create candles with one outlier
        volumes = [1000] * 49 + [10000]  # One extreme outlier
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(volumes[i])),
            )
            for i in range(50)
        ]

        current_volume = Decimal("2000")

        median_results = VolumeAnalyzer.analyze_volume_vs_baselines(
            current_volume=current_volume,
            candles=candles,
            windows={"test": 50},
            baseline_method="median",
        )

        mean_results = VolumeAnalyzer.analyze_volume_vs_baselines(
            current_volume=current_volume,
            candles=candles,
            windows={"test": 50},
            baseline_method="mean",
        )

        # Median should be resistant to outlier
        assert median_results["test"].baseline < mean_results["test"].baseline
        assert median_results["test"].multiplier > mean_results["test"].multiplier

    def test_analyze_insufficient_data(self):
        """Test handling insufficient data."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal("1000"),
            )
            for i in range(10)
        ]

        results = VolumeAnalyzer.analyze_volume_vs_baselines(
            current_volume=Decimal("2000"),
            candles=candles,
            windows={"large": 100},
        )

        assert results["large"].insufficient_data
        assert results["large"].multiplier == Decimal("0")
        assert results["large"].percentile == 0.0

    def test_analyze_invalid_baseline_method(self):
        """Test error handling for invalid baseline method."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal("1000"),
            )
            for i in range(50)
        ]

        with pytest.raises(ValueError, match="Invalid baseline_method"):
            VolumeAnalyzer.analyze_volume_vs_baselines(
                current_volume=Decimal("2000"),
                candles=candles,
                windows={"test": 20},
                baseline_method="invalid",  # type: ignore
            )


class TestVolumePercentile:
    """Test volume percentile calculation."""

    def test_percentile_median_volume(self):
        """Test percentile for median volume."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(1000 + i)),
            )
            for i in range(100)
        ]

        # Middle value should be around 50th percentile
        median_volume = Decimal("1050")
        percentile = VolumeAnalyzer.calculate_volume_percentile(median_volume, candles)

        assert 45 <= percentile <= 55

    def test_percentile_extreme_values(self):
        """Test percentile for extreme values."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal("1000"),
            )
            for i in range(100)
        ]

        # Very high volume
        high_percentile = VolumeAnalyzer.calculate_volume_percentile(
            Decimal("10000"), candles
        )
        assert high_percentile == 100.0

        # Very low volume
        low_percentile = VolumeAnalyzer.calculate_volume_percentile(
            Decimal("1"), candles
        )
        assert low_percentile == 0.0

    def test_percentile_empty_candles(self):
        """Test percentile with empty candles."""
        percentile = VolumeAnalyzer.calculate_volume_percentile(
            Decimal("1000"), []
        )
        assert percentile == 0.0


class TestVolumeZScore:
    """Test volume z-score calculation."""

    def test_zscore_at_mean(self):
        """Test z-score for volume at mean."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal("1000"),  # All same volume
            )
            for i in range(100)
        ]

        zscore = VolumeAnalyzer.calculate_volume_zscore(Decimal("1000"), candles)

        # All volumes the same, std=0, should return 0
        assert zscore == 0.0

    def test_zscore_extreme_values(self):
        """Test z-score for extreme values."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candles = [
            create_test_candle(
                timestamp=base_time + timedelta(hours=i),
                volume=Decimal(str(1000 + i)),
            )
            for i in range(100)
        ]

        # Very high volume should have positive z-score
        high_zscore = VolumeAnalyzer.calculate_volume_zscore(
            Decimal("10000"), candles
        )
        assert high_zscore > 3

        # Very low volume should have negative z-score
        low_zscore = VolumeAnalyzer.calculate_volume_zscore(Decimal("1"), candles)
        assert low_zscore < -3

    def test_zscore_insufficient_data(self):
        """Test z-score with insufficient data."""
        base_time = datetime(2024, 1, 1, 0, 0)
        candle = create_test_candle(
            timestamp=base_time,
            volume=Decimal("1000"),
        )

        # Single candle - can't calculate std
        zscore = VolumeAnalyzer.calculate_volume_zscore(
            Decimal("2000"), [candle]
        )
        assert zscore == 0.0

        # Empty list
        zscore = VolumeAnalyzer.calculate_volume_zscore(
            Decimal("2000"), []
        )
        assert zscore == 0.0
