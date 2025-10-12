"""Tests for spike detection."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from laakhay.ta.models import Candle
from laakhay.ta.signals.spikes import (
    CombinedSpikeDetector,
    PriceSpikeDetector,
    VolumeSpikeDetector,
)


def create_candle(
    symbol: str = "BTCUSDT",
    timestamp: datetime | None = None,
    open: float = 100.0,
    high: float = 110.0,
    low: float = 90.0,
    close: float = 105.0,
    volume: float = 1000.0,
) -> Candle:
    """Helper to create test candles."""
    if timestamp is None:
        timestamp = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    return Candle(
        symbol=symbol,
        timestamp=timestamp,
        open=Decimal(str(open)),
        high=Decimal(str(high)),
        low=Decimal(str(low)),
        close=Decimal(str(close)),
        volume=Decimal(str(volume)),
        is_closed=True,
    )


class TestPriceSpikeDetector:
    """Test price spike detection."""

    def test_bullish_spike_detection(self):
        """Test bullish spike detection."""
        # Close > open, so bullish
        # Spike = (high - low) / low * 100 = (110 - 90) / 90 = 22.22%
        candle = create_candle(open=100, high=110, low=90, close=105)

        result = PriceSpikeDetector.detect_spike(candle, threshold_pct=5.0)

        assert result.direction == "bullish"
        assert result.is_spike is True
        assert result.strength == "extreme"  # >10%
        assert float(result.spike_pct) > 22.0

    def test_bearish_spike_detection(self):
        """Test bearish spike detection."""
        # Close < open, so bearish
        # Spike = (high - low) / high * 100 = (110 - 90) / 110 = 18.18%
        candle = create_candle(open=105, high=110, low=90, close=95)

        result = PriceSpikeDetector.detect_spike(candle, threshold_pct=5.0)

        assert result.direction == "bearish"
        assert result.is_spike is True
        assert result.strength == "extreme"  # >10%
        assert float(result.spike_pct) > 18.0

    def test_no_spike_below_threshold(self):
        """Test no spike when below threshold."""
        # Small range: (102 - 98) / 98 = 4.08%
        candle = create_candle(open=100, high=102, low=98, close=101)

        result = PriceSpikeDetector.detect_spike(candle, threshold_pct=5.0)

        assert result.direction == "none"  # Below threshold
        assert result.is_spike is False
        assert result.strength == "moderate"

    def test_series_detection(self):
        """Test series-first detection."""
        candles = [
            create_candle(open=100, high=110, low=90, close=105),  # Bullish spike
            create_candle(open=100, high=102, low=98, close=101),  # No spike
            create_candle(open=105, high=110, low=90, close=95),  # Bearish spike
        ]

        results = PriceSpikeDetector.detect_spikes_series(candles, threshold_pct=5.0)

        assert len(results) == 3
        assert results[0].is_spike is True
        assert results[0].direction == "bullish"
        assert results[1].is_spike is False
        assert results[2].is_spike is True
        assert results[2].direction == "bearish"


class TestVolumeSpikeDetector:
    """Test volume spike detection."""

    def test_volume_baseline_median(self):
        """Test median baseline calculation."""
        candles = [create_candle(volume=v) for v in [100, 200, 150, 180, 120]]

        baseline = VolumeSpikeDetector.calculate_volume_baseline(candles, method="median")

        assert baseline == Decimal("150")

    def test_volume_baseline_mean(self):
        """Test mean baseline calculation."""
        candles = [create_candle(volume=v) for v in [100, 200, 150]]

        baseline = VolumeSpikeDetector.calculate_volume_baseline(candles, method="mean")

        assert baseline == Decimal("150")

    def test_volume_spike_detection(self):
        """Test volume spike detection."""
        historical = [create_candle(volume=100) for _ in range(20)]
        current = create_candle(volume=300)

        result = VolumeSpikeDetector.detect_volume_spike(
            candle=current,
            historical_candles=historical,
            multiplier_threshold=2.0,
        )

        assert result.is_spike is True
        assert result.multiplier == Decimal("3.0")  # 300 / 100
        assert result.baseline_volume == Decimal("100")
        assert result.percentile == 100.0  # Higher than all historical

    def test_no_volume_spike(self):
        """Test no spike when below threshold."""
        historical = [create_candle(volume=100) for _ in range(20)]
        current = create_candle(volume=150)

        result = VolumeSpikeDetector.detect_volume_spike(
            candle=current,
            historical_candles=historical,
            multiplier_threshold=2.0,
        )

        assert result.is_spike is False
        assert result.multiplier == Decimal("1.5")

    def test_volume_series_detection(self):
        """Test series-first volume detection."""
        # First 20 candles with volume 100, then 5 with increasing volume
        candles = [create_candle(volume=100) for _ in range(20)]
        candles.extend(
            [
                create_candle(volume=150),
                create_candle(volume=200),
                create_candle(volume=300),
            ]
        )

        results = VolumeSpikeDetector.detect_volume_spikes_series(
            candles, window_size=20, multiplier_threshold=2.0
        )

        # Should have results for candles 20, 21, 22
        assert len(results) == 3
        assert results[0].is_spike is False  # 1.5x
        assert results[1].is_spike is False  # 2.0x exactly (not >=)
        assert results[2].is_spike is True  # 3.0x


class TestCombinedSpikeDetector:
    """Test combined spike detection."""

    def test_combined_spike(self):
        """Test combined price + volume spike."""
        historical = [create_candle(volume=100) for _ in range(20)]
        current = create_candle(open=100, high=110, low=90, close=105, volume=300)

        result = CombinedSpikeDetector.detect_combined_spike(
            candle=current,
            historical_candles=historical,
            price_threshold=5.0,
            volume_multiplier=2.0,
        )

        assert result.alert_type == "combined"
        assert result.should_alert is True
        assert result.price_spike.is_spike is True
        assert result.volume_spike.is_spike is True

    def test_price_only_spike(self):
        """Test price spike without volume spike."""
        historical = [create_candle(volume=100) for _ in range(20)]
        current = create_candle(open=100, high=110, low=90, close=105, volume=120)

        result = CombinedSpikeDetector.detect_combined_spike(
            candle=current,
            historical_candles=historical,
            price_threshold=5.0,
            volume_multiplier=2.0,
            require_both=False,
        )

        assert result.alert_type == "price"
        assert result.should_alert is True

    def test_volume_only_spike(self):
        """Test volume spike without price spike."""
        historical = [create_candle(volume=100) for _ in range(20)]
        current = create_candle(open=100, high=102, low=98, close=101, volume=300)

        result = CombinedSpikeDetector.detect_combined_spike(
            candle=current,
            historical_candles=historical,
            price_threshold=5.0,
            volume_multiplier=2.0,
            require_both=False,
        )

        assert result.alert_type == "volume"
        assert result.should_alert is True

    def test_require_both_flag(self):
        """Test require_both flag blocks single spike types."""
        historical = [create_candle(volume=100) for _ in range(20)]
        current = create_candle(open=100, high=110, low=90, close=105, volume=120)

        result = CombinedSpikeDetector.detect_combined_spike(
            candle=current,
            historical_candles=historical,
            price_threshold=5.0,
            volume_multiplier=2.0,
            require_both=True,
        )

        assert result.alert_type == "price"
        assert result.should_alert is False  # require_both=True, only price spike
