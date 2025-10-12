"""Correlation analysis for price series."""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from laakhay.ta.models import Candle


class CorrelationResult(BaseModel):
    """Result from correlation analysis between two price series."""

    model_config = ConfigDict(frozen=True)

    asset1: str = Field(description="First asset identifier")
    asset2: str = Field(description="Second asset identifier")
    correlation: float = Field(description="Pearson correlation coefficient (-1 to 1)")
    lookback_periods: int = Field(description="Number of periods used")
    start_timestamp: datetime = Field(description="Start of analysis period")
    end_timestamp: datetime = Field(description="End of analysis period")
    data_points: int = Field(description="Number of data points used")


class CrossAssetCorrelationResult(BaseModel):
    """Result from cross-asset correlation analysis."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(description="Analysis timestamp")
    correlation: float = Field(description="Pearson correlation coefficient (-1 to 1)")
    lookback_periods: int = Field(description="Number of periods used")
    is_significant: bool = Field(description="Whether correlation meets significance threshold")
    strength: Literal["weak", "moderate", "strong"] = Field(
        description="Qualitative correlation strength"
    )


class CorrelationAnalyzer:
    """Pure stateless correlation analysis.

    Provides Pearson correlation calculation for price series
    following laakhay/ta's stateless, series-first design.
    """

    @staticmethod
    def calculate_pearson_correlation(series1: Sequence[float], series2: Sequence[float]) -> float:
        """Calculate Pearson correlation coefficient.

        Args:
            series1: First data series
            series2: Second data series (must be same length)

        Returns:
            Pearson correlation coefficient (-1 to 1)

        Raises:
            ValueError: If series have different lengths or insufficient data

        Example:
            >>> prices1 = [100, 102, 105, 103, 106]
            >>> prices2 = [50, 51, 53, 52, 54]
            >>> corr = CorrelationAnalyzer.calculate_pearson_correlation(
            ...     prices1, prices2
            ... )
            >>> print(f"Correlation: {corr:.4f}")
        """
        if len(series1) != len(series2):
            raise ValueError(f"Series must have same length: {len(series1)} != {len(series2)}")

        if len(series1) < 2:
            raise ValueError(f"Need at least 2 data points, got {len(series1)}")

        n = len(series1)

        # Calculate means
        mean1 = sum(series1) / n
        mean2 = sum(series2) / n

        # Calculate correlation components
        numerator = sum(
            (x1 - mean1) * (x2 - mean2) for x1, x2 in zip(series1, series2, strict=True)
        )
        sum_sq1 = sum((x1 - mean1) ** 2 for x1 in series1)
        sum_sq2 = sum((x2 - mean2) ** 2 for x2 in series2)

        denominator = (sum_sq1 * sum_sq2) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    @staticmethod
    def correlate_candle_series(
        candles1: Sequence[Candle],
        candles2: Sequence[Candle],
        price_field: Literal["close", "open", "high", "low"] = "close",
        asset1_name: str = "asset1",
        asset2_name: str = "asset2",
    ) -> CorrelationResult:
        """Calculate correlation between two candle series.

        Args:
            candles1: First candle series
            candles2: Second candle series (must be same length)
            price_field: Which price field to use
            asset1_name: Name/identifier for first asset
            asset2_name: Name/identifier for second asset

        Returns:
            CorrelationResult with detailed analysis

        Example:
            >>> btc_candles = [...]  # BTC candles
            >>> eth_candles = [...]  # ETH candles
            >>> result = CorrelationAnalyzer.correlate_candle_series(
            ...     btc_candles, eth_candles,
            ...     asset1_name="BTC", asset2_name="ETH"
            ... )
            >>> print(f"{result.asset1} vs {result.asset2}: {result.correlation:.3f}")
        """
        if len(candles1) != len(candles2):
            raise ValueError(
                f"Candle series must have same length: {len(candles1)} != {len(candles2)}"
            )

        if not candles1:
            raise ValueError("Candle series cannot be empty")

        # Extract price series
        prices1 = [float(getattr(c, price_field)) for c in candles1]
        prices2 = [float(getattr(c, price_field)) for c in candles2]

        correlation = CorrelationAnalyzer.calculate_pearson_correlation(prices1, prices2)

        return CorrelationResult(
            asset1=asset1_name,
            asset2=asset2_name,
            correlation=correlation,
            lookback_periods=len(candles1),
            start_timestamp=candles1[0].timestamp,
            end_timestamp=candles1[-1].timestamp,
            data_points=len(candles1),
        )

    @staticmethod
    def detect_correlation_change(
        current_candles1: Sequence[Candle],
        current_candles2: Sequence[Candle],
        significance_threshold: float = 0.7,
        price_field: Literal["close", "open", "high", "low"] = "close",
    ) -> CrossAssetCorrelationResult:
        """Detect significant correlation in current window.

        Args:
            current_candles1: Current window for asset 1
            current_candles2: Current window for asset 2
            significance_threshold: Minimum |correlation| to be significant
            price_field: Which price field to use

        Returns:
            CrossAssetCorrelationResult with significance assessment

        Example:
            >>> result = CorrelationAnalyzer.detect_correlation_change(
            ...     btc_recent, eth_recent,
            ...     significance_threshold=0.7
            ... )
            >>> if result.is_significant:
            ...     print(f"{result.strength.upper()} correlation detected")
        """
        if not current_candles1 or not current_candles2:
            raise ValueError("Candle series cannot be empty")

        prices1 = [float(getattr(c, price_field)) for c in current_candles1]
        prices2 = [float(getattr(c, price_field)) for c in current_candles2]

        correlation = CorrelationAnalyzer.calculate_pearson_correlation(prices1, prices2)

        abs_corr = abs(correlation)
        is_significant = abs_corr >= significance_threshold

        # Classify strength
        if abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.4:
            strength = "moderate"
        else:
            strength = "weak"

        return CrossAssetCorrelationResult(
            timestamp=current_candles1[-1].timestamp,
            correlation=correlation,
            lookback_periods=len(current_candles1),
            is_significant=is_significant,
            strength=strength,
        )

    @staticmethod
    def rolling_correlation_series(
        candles1: Sequence[Candle],
        candles2: Sequence[Candle],
        window_size: int,
        price_field: Literal["close", "open", "high", "low"] = "close",
    ) -> list[CrossAssetCorrelationResult]:
        """Calculate rolling correlation over time.

        Args:
            candles1: First candle series
            candles2: Second candle series (must be same length)
            window_size: Size of rolling window
            price_field: Which price field to use

        Returns:
            List of CrossAssetCorrelationResult, one per window

        Example:
            >>> results = CorrelationAnalyzer.rolling_correlation_series(
            ...     btc_candles, eth_candles,
            ...     window_size=30
            ... )
            >>> for r in results[-5:]:  # Last 5 windows
            ...     print(f"{r.timestamp}: {r.correlation:.3f} ({r.strength})")
        """
        if len(candles1) != len(candles2):
            raise ValueError(
                f"Candle series must have same length: {len(candles1)} != {len(candles2)}"
            )

        if window_size < 2:
            raise ValueError(f"Window size must be >= 2, got {window_size}")

        if len(candles1) < window_size:
            raise ValueError(f"Need at least {window_size} candles, got {len(candles1)}")

        results = []
        for i in range(window_size, len(candles1) + 1):
            window1 = candles1[i - window_size : i]
            window2 = candles2[i - window_size : i]

            result = CorrelationAnalyzer.detect_correlation_change(
                window1, window2, price_field=price_field
            )
            results.append(result)

        return results
