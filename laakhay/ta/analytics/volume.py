"""
Volume Analysis Module

Provides stateless volume analysis tools for cryptocurrency market data.
Implements volume profiling, baseline comparisons, and multi-window analysis.

Design:
- Stateless: Pure functions with @staticmethod
- Series-first: Returns structured data for downstream processing
- Type-safe: Pydantic models for all results
- Deterministic: Same inputs always produce same outputs
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from statistics import mean, median, stdev
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from laakhay.ta.models import Candle


class VolumeWindowAnalysis(BaseModel):
    """Analysis of volume against a specific time window."""

    model_config = ConfigDict(frozen=True)

    window_name: str = Field(description="Name of the time window (e.g., 'short', 'medium', 'long')")
    window_size: int = Field(gt=0, description="Size of the window in candles")
    baseline: Decimal = Field(ge=0, description="Calculated baseline volume for this window")
    multiplier: Decimal = Field(ge=0, description="Current volume as multiplier of baseline")
    percentile: float = Field(ge=0, le=100, description="Percentile rank of current volume (0-100)")
    zscore: float = Field(description="Z-score of current volume (standard deviations from mean)")
    median: Decimal = Field(ge=0, description="Median volume for this window")
    mean: Decimal = Field(ge=0, description="Mean volume for this window")
    std: Decimal = Field(ge=0, description="Standard deviation of volume for this window")
    min: Decimal = Field(ge=0, description="Minimum volume in this window")
    max: Decimal = Field(ge=0, description="Maximum volume in this window")
    insufficient_data: bool = Field(description="Whether window had insufficient data for analysis")


class VolumeAnalyzer:
    """Stateless volume analysis utilities.
    
    Provides methods for:
    - Volume statistics calculation across multiple time windows
    - Volume baseline comparison (vs median/mean)
    - Multi-window volume analysis
    - Volume profiling
    
    Example:
        >>> candles = [...]  # Historical candle data
        >>> current_volume = Decimal("1000000")
        >>>
        >>> # Analyze against multiple windows
        >>> results = VolumeAnalyzer.analyze_volume_vs_baselines(
        ...     current_volume=current_volume,
        ...     candles=candles,
        ...     windows={"short": 20, "medium": 100, "long": 1000}
        ... )
        >>>
        >>> for window_name, analysis in results.items():
        ...     if analysis.multiplier > 2:
        ...         print(f"{window_name}: {analysis.multiplier}x baseline")
    """

    @staticmethod
    def calculate_volume_statistics(
        candles: Sequence[Candle],
        windows: dict[str, int] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Calculate volume statistics across multiple time windows.
        
        Args:
            candles: Historical candle data (most recent last)
            windows: Dict of window_name -> window_size (default: {"short": 20, "medium": 100})
            
        Returns:
            Dict of window_name -> statistics dict with keys:
                - median (Decimal)
                - mean (Decimal)
                - std (Decimal)
                - min (Decimal)
                - max (Decimal)
                - insufficient_data (bool)
            
        Example:
            >>> stats = VolumeAnalyzer.calculate_volume_statistics(
            ...     candles,
            ...     windows={"short": 20, "medium": 100, "long": 1000}
            ... )
            >>> print(stats["short"]["median"])
        """
        if windows is None:
            windows = {"short": 20, "medium": 100}

        results = {}

        for window_name, window_size in windows.items():
            if len(candles) < window_size:
                results[window_name] = {
                    "median": Decimal("0"),
                    "mean": Decimal("0"),
                    "std": Decimal("0"),
                    "min": Decimal("0"),
                    "max": Decimal("0"),
                    "insufficient_data": True,
                }
                continue

            window_candles = candles[-window_size:]
            volumes = [float(c.volume) for c in window_candles]

            results[window_name] = {
                "median": Decimal(str(median(volumes))),
                "mean": Decimal(str(mean(volumes))),
                "std": Decimal(str(stdev(volumes))) if len(volumes) > 1 else Decimal("0"),
                "min": Decimal(str(min(volumes))),
                "max": Decimal(str(max(volumes))),
                "insufficient_data": False,
            }

        return results

    @staticmethod
    def analyze_volume_vs_baselines(
        current_volume: Decimal,
        candles: Sequence[Candle],
        windows: dict[str, int],
        baseline_method: Literal["median", "mean"] = "median",
    ) -> dict[str, VolumeWindowAnalysis]:
        """Analyze current volume against multiple baseline windows.
        
        Args:
            current_volume: Current volume to analyze
            candles: Historical candles (most recent last, excluding current)
            windows: Dict of window_name -> window_size
            baseline_method: Method for baseline calculation ("median" or "mean")
            
        Returns:
            Dict of window_name -> VolumeWindowAnalysis
            
        Raises:
            ValueError: If baseline_method is invalid
            
        Example:
            >>> analysis = VolumeAnalyzer.analyze_volume_vs_baselines(
            ...     current_volume=Decimal("1000000"),
            ...     candles=historical_candles,
            ...     windows={"short": 20, "medium": 100, "long": 1000}
            ... )
            >>>
            >>> for name, result in analysis.items():
            ...     if result.multiplier > 2:
            ...         print(f"{name} window: {result.multiplier}x baseline")
        """
        if baseline_method not in ("median", "mean"):
            raise ValueError(f"Invalid baseline_method: {baseline_method}. Must be 'median' or 'mean'.")

        stats = VolumeAnalyzer.calculate_volume_statistics(candles, windows)

        results = {}
        for window_name, window_stats in stats.items():
            if window_stats["insufficient_data"]:
                results[window_name] = VolumeWindowAnalysis(
                    window_name=window_name,
                    window_size=windows[window_name],
                    baseline=Decimal("0"),
                    multiplier=Decimal("0"),
                    percentile=0.0,
                    zscore=0.0,
                    median=Decimal("0"),
                    mean=Decimal("0"),
                    std=Decimal("0"),
                    min=Decimal("0"),
                    max=Decimal("0"),
                    insufficient_data=True,
                )
                continue

            baseline = window_stats[baseline_method]
            multiplier = current_volume / baseline if baseline > 0 else Decimal("0")

            # Calculate percentile
            window_size = windows[window_name]
            window_candles = candles[-window_size:]
            volumes = [float(c.volume) for c in window_candles]
            count_below = sum(1 for v in volumes if v < float(current_volume))
            percentile = (count_below / len(volumes)) * 100

            # Calculate z-score
            mean_vol = window_stats["mean"]
            std_vol = window_stats["std"]
            zscore = float((current_volume - mean_vol) / std_vol) if std_vol > 0 else 0.0

            results[window_name] = VolumeWindowAnalysis(
                window_name=window_name,
                window_size=window_size,
                baseline=baseline,
                multiplier=multiplier,
                percentile=percentile,
                zscore=zscore,
                median=window_stats["median"],
                mean=mean_vol,
                std=std_vol,
                min=window_stats["min"],
                max=window_stats["max"],
                insufficient_data=False,
            )

        return results

    @staticmethod
    def calculate_volume_percentile(
        volume: Decimal,
        candles: Sequence[Candle],
    ) -> float:
        """Calculate percentile rank of a volume value.
        
        Args:
            volume: Volume value to rank
            candles: Historical candles to compare against
            
        Returns:
            Percentile rank (0-100)
            
        Example:
            >>> percentile = VolumeAnalyzer.calculate_volume_percentile(
            ...     volume=Decimal("1000000"),
            ...     candles=historical_candles
            ... )
            >>> if percentile > 95:
            ...     print("Volume in top 5%")
        """
        if not candles:
            return 0.0

        volumes = [float(c.volume) for c in candles]
        count_below = sum(1 for v in volumes if v < float(volume))
        return (count_below / len(volumes)) * 100

    @staticmethod
    def calculate_volume_zscore(
        volume: Decimal,
        candles: Sequence[Candle],
    ) -> float:
        """Calculate z-score of a volume value.
        
        Args:
            volume: Volume value to score
            candles: Historical candles to compare against
            
        Returns:
            Z-score (standard deviations from mean)
            
        Example:
            >>> zscore = VolumeAnalyzer.calculate_volume_zscore(
            ...     volume=Decimal("1000000"),
            ...     candles=historical_candles
            ... )
            >>> if zscore > 3:
            ...     print("Volume more than 3 std devs above mean")
        """
        if not candles or len(candles) < 2:
            return 0.0

        volumes = [float(c.volume) for c in candles]
        mean_vol = mean(volumes)
        std_vol = stdev(volumes)

        if std_vol == 0:
            return 0.0

        return (float(volume) - mean_vol) / std_vol
