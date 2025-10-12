"""Price and volume spike detection.

Stateless spike detection following laakhay/ta principles:
- Pure functions (static methods)
- Series-first (return complete time series)
- Pydantic models for results
- No I/O or state management
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from statistics import mean, median, stdev
from typing import Literal

from pydantic import BaseModel, Field

from ..models import Candle


class PriceSpikeResult(BaseModel):
    """Result of price spike detection for a single candle."""

    timestamp: datetime
    spike_pct: Decimal = Field(ge=0, description="Spike percentage (0-100+)")
    direction: Literal["bullish", "bearish", "none"]
    strength: Literal["weak", "moderate", "strong", "extreme"]

    @property
    def is_spike(self) -> bool:
        """Check if this represents an actual spike (not 'none')."""
        return self.direction != "none"


class VolumeSpikeResult(BaseModel):
    """Result of volume spike detection for a single candle."""

    timestamp: datetime
    current_volume: Decimal
    baseline_volume: Decimal
    multiplier: Decimal = Field(ge=0, description="Volume multiplier vs baseline")
    percentile: float = Field(ge=0, le=100, description="Percentile rank (0-100)")
    zscore: float = Field(description="Z-score (standard deviations from mean)")
    is_spike: bool = Field(description="Whether volume spike threshold was exceeded")


class CombinedSpikeResult(BaseModel):
    """Result of combined price + volume spike detection."""

    timestamp: datetime
    alert_type: Literal["price", "volume", "combined", "none"]
    should_alert: bool
    price_spike: PriceSpikeResult
    volume_spike: VolumeSpikeResult


class PriceSpikeDetector:
    """Stateless price spike detection.

    Detects price spikes within individual candles based on high-low range
    relative to candle direction (bullish/bearish).
    """

    @staticmethod
    def detect_spike(
        candle: Candle,
        threshold_pct: float = 5.0,
    ) -> PriceSpikeResult:
        """Detect price spike in a single candle.

        Calculation:
            - Bullish (close > open): spike_pct = (high - low) / low * 100
            - Bearish (close < open): spike_pct = (high - low) / high * 100
            - Neutral (close == open): spike_pct = 0

        Args:
            candle: OHLC candle data
            threshold_pct: Minimum spike percentage to classify as spike

        Returns:
            PriceSpikeResult with spike percentage, direction, and strength

        Example:
            >>> from laakhay.ta.signals.spikes import PriceSpikeDetector
            >>> result = PriceSpikeDetector.detect_spike(candle, threshold_pct=5.0)
            >>> if result.is_spike:
            ...     print(f"{result.direction}: {result.spike_pct}% ({result.strength})")
        """
        if candle.low == 0 or candle.high == 0:
            return PriceSpikeResult(
                timestamp=candle.timestamp,
                spike_pct=Decimal("0"),
                direction="none",
                strength="weak",
            )

        # Determine direction and calculate spike
        if candle.close > candle.open:
            # Bullish: measure from low
            spike_pct = float((candle.high - candle.low) / candle.low * 100)
            direction = "bullish"
        elif candle.close < candle.open:
            # Bearish: measure from high
            spike_pct = float((candle.high - candle.low) / candle.high * 100)
            direction = "bearish"
        else:
            spike_pct = 0.0
            direction = "none"

        # Classify strength
        if spike_pct < 2.0:
            strength = "weak"
        elif spike_pct < 5.0:
            strength = "moderate"
        elif spike_pct < 10.0:
            strength = "strong"
        else:
            strength = "extreme"

        return PriceSpikeResult(
            timestamp=candle.timestamp,
            spike_pct=Decimal(str(round(spike_pct, 4))),
            direction=direction if spike_pct >= threshold_pct else "none",
            strength=strength,
        )

    @staticmethod
    def detect_spikes_series(
        candles: Sequence[Candle],
        threshold_pct: float = 5.0,
    ) -> list[PriceSpikeResult]:
        """Detect spikes across a candle series (series-first).

        Returns complete time series for all candles.

        Args:
            candles: Sequence of OHLC candles (chronological order)
            threshold_pct: Minimum spike percentage to classify as spike

        Returns:
            List of PriceSpikeResult for each candle

        Example:
            >>> results = PriceSpikeDetector.detect_spikes_series(candles)
            >>> spikes = [r for r in results if r.is_spike]
        """
        return [PriceSpikeDetector.detect_spike(candle, threshold_pct) for candle in candles]


class VolumeSpikeDetector:
    """Stateless volume spike detection.

    Detects volume spikes by comparing current volume against historical baselines.
    """

    @staticmethod
    def calculate_volume_baseline(
        historical_candles: Sequence[Candle],
        method: Literal["median", "mean", "ema"] = "median",
        ema_alpha: float = 0.1,
    ) -> Decimal:
        """Calculate volume baseline from historical candles.

        Args:
            historical_candles: Historical candle data (excluding current)
            method: Baseline calculation method
            ema_alpha: Smoothing factor for EMA (if method="ema")

        Returns:
            Baseline volume
        """
        if not historical_candles:
            return Decimal("0")

        volumes = [float(c.volume) for c in historical_candles]

        if method == "median":
            return Decimal(str(median(volumes)))
        elif method == "mean":
            return Decimal(str(mean(volumes)))
        elif method == "ema":
            ema = volumes[0]
            for v in volumes[1:]:
                ema = ema_alpha * v + (1 - ema_alpha) * ema
            return Decimal(str(ema))
        else:
            raise ValueError(f"Unknown baseline method: {method}")

    @staticmethod
    def detect_volume_spike(
        candle: Candle,
        historical_candles: Sequence[Candle],
        multiplier_threshold: float = 2.0,
        baseline_method: Literal["median", "mean", "ema"] = "median",
    ) -> VolumeSpikeResult:
        """Detect volume spike vs historical baseline.

        Args:
            candle: Current candle
            historical_candles: Historical candles for baseline (excluding current)
            multiplier_threshold: Minimum multiplier to trigger spike
            baseline_method: How to calculate baseline

        Returns:
            VolumeSpikeResult with detailed volume analysis

        Example:
            >>> result = VolumeSpikeDetector.detect_volume_spike(
            ...     candle=current_candle,
            ...     historical_candles=candles[:-1],
            ...     multiplier_threshold=2.0
            ... )
            >>> if result.is_spike:
            ...     print(f"Volume spike: {result.multiplier}x baseline")
        """
        if not historical_candles:
            return VolumeSpikeResult(
                timestamp=candle.timestamp,
                current_volume=candle.volume,
                baseline_volume=Decimal("0"),
                multiplier=Decimal("0"),
                percentile=0.0,
                zscore=0.0,
                is_spike=False,
            )

        baseline = VolumeSpikeDetector.calculate_volume_baseline(
            historical_candles, method=baseline_method
        )

        if baseline == 0:
            return VolumeSpikeResult(
                timestamp=candle.timestamp,
                current_volume=candle.volume,
                baseline_volume=baseline,
                multiplier=Decimal("0"),
                percentile=0.0,
                zscore=0.0,
                is_spike=False,
            )

        multiplier = candle.volume / baseline
        is_spike = multiplier > Decimal(str(multiplier_threshold))

        # Calculate percentile
        volumes = [float(c.volume) for c in historical_candles]
        volumes_sorted = sorted(volumes)
        percentile = (
            sum(1 for v in volumes_sorted if v < float(candle.volume)) / len(volumes_sorted)
        ) * 100

        # Calculate z-score
        mean_vol = mean(volumes)
        std_vol = stdev(volumes) if len(volumes) > 1 else 0
        zscore = ((float(candle.volume) - mean_vol) / std_vol) if std_vol > 0 else 0.0

        return VolumeSpikeResult(
            timestamp=candle.timestamp,
            current_volume=candle.volume,
            baseline_volume=baseline,
            multiplier=multiplier,
            percentile=percentile,
            zscore=zscore,
            is_spike=is_spike,
        )

    @staticmethod
    def detect_volume_spikes_series(
        candles: Sequence[Candle],
        window_size: int = 20,
        multiplier_threshold: float = 2.0,
        baseline_method: Literal["median", "mean", "ema"] = "median",
    ) -> list[VolumeSpikeResult]:
        """Detect volume spikes across a series (series-first).

        Returns results for all candles where enough history exists.

        Args:
            candles: Sequence of candles (chronological order)
            window_size: Number of candles for baseline calculation
            multiplier_threshold: Minimum multiplier to trigger
            baseline_method: Baseline calculation method

        Returns:
            List of VolumeSpikeResult for candles starting at index window_size
        """
        if len(candles) < window_size + 1:
            return []

        results = []
        for i in range(window_size, len(candles)):
            result = VolumeSpikeDetector.detect_volume_spike(
                candle=candles[i],
                historical_candles=candles[i - window_size : i],
                multiplier_threshold=multiplier_threshold,
                baseline_method=baseline_method,
            )
            results.append(result)

        return results


class CombinedSpikeDetector:
    """Combined price and volume spike detection."""

    @staticmethod
    def detect_combined_spike(
        candle: Candle,
        historical_candles: Sequence[Candle],
        price_threshold: float = 5.0,
        volume_multiplier: float = 2.0,
        require_both: bool = False,
    ) -> CombinedSpikeResult:
        """Detect combined price + volume spike.

        Args:
            candle: Current candle
            historical_candles: Historical candles for volume baseline
            price_threshold: Minimum price spike percentage
            volume_multiplier: Minimum volume multiplier
            require_both: If True, require both price AND volume spike

        Returns:
            CombinedSpikeResult with comprehensive spike analysis
        """
        # Detect price spike
        price_result = PriceSpikeDetector.detect_spike(candle, price_threshold)

        # Detect volume spike
        volume_result = VolumeSpikeDetector.detect_volume_spike(
            candle=candle,
            historical_candles=historical_candles,
            multiplier_threshold=volume_multiplier,
        )

        # Determine alert type
        price_spike_detected = price_result.is_spike
        volume_spike_detected = volume_result.is_spike

        if price_spike_detected and volume_spike_detected:
            alert_type = "combined"
        elif price_spike_detected:
            alert_type = "price"
        elif volume_spike_detected:
            alert_type = "volume"
        else:
            alert_type = "none"

        # Check if we should trigger based on require_both flag
        should_alert = alert_type == "combined" or (
            not require_both and alert_type in ["price", "volume"]
        )

        return CombinedSpikeResult(
            timestamp=candle.timestamp,
            alert_type=alert_type,
            should_alert=should_alert,
            price_spike=price_result,
            volume_spike=volume_result,
        )

    @staticmethod
    def detect_combined_spikes_series(
        candles: Sequence[Candle],
        window_size: int = 20,
        price_threshold: float = 5.0,
        volume_multiplier: float = 2.0,
        require_both: bool = False,
    ) -> list[CombinedSpikeResult]:
        """Detect combined spikes across a series (series-first).

        Args:
            candles: Sequence of candles
            window_size: Number of candles for volume baseline
            price_threshold: Minimum price spike percentage
            volume_multiplier: Minimum volume multiplier
            require_both: If True, require both price AND volume spike

        Returns:
            List of CombinedSpikeResult for all analyzable candles
        """
        if len(candles) < window_size + 1:
            return []

        results = []
        for i in range(window_size, len(candles)):
            result = CombinedSpikeDetector.detect_combined_spike(
                candle=candles[i],
                historical_candles=candles[i - window_size : i],
                price_threshold=price_threshold,
                volume_multiplier=volume_multiplier,
                require_both=require_both,
            )
            results.append(result)

        return results
