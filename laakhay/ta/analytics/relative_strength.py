"""Relative strength analysis for comparing asset performance."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from laakhay.ta.models import Candle


class RelativeStrengthResult(BaseModel):
    """Result of relative strength calculation."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(description="Analysis timestamp")
    symbol_change_pct: Decimal = Field(description="Symbol percentage change")
    base_change_pct: Decimal = Field(description="Base asset percentage change")
    relative_strength: Decimal = Field(
        description="Relative strength (symbol - base)"
    )
    divergence_type: Literal["bullish", "bearish", "none"] = Field(
        description="Type of divergence detected"
    )

    @property
    def is_outperforming(self) -> bool:
        """Check if symbol is outperforming base."""
        return self.relative_strength > 0

    @property
    def strength_category(
        self,
    ) -> Literal["strong_out", "moderate_out", "neutral", "moderate_under", "strong_under"]:
        """Categorize relative strength."""
        rs = float(self.relative_strength)
        if rs > 5:
            return "strong_out"
        elif rs > 2:
            return "moderate_out"
        elif rs < -5:
            return "strong_under"
        elif rs < -2:
            return "moderate_under"
        else:
            return "neutral"


class RelativeStrengthAnalyzer:
    """Stateless relative strength analysis.

    Compares asset performance against a base asset to identify
    relative strength and divergence patterns.
    """

    @staticmethod
    def calculate_relative_strength(
        symbol_start_price: Decimal,
        symbol_current_price: Decimal,
        base_start_price: Decimal,
        base_current_price: Decimal,
        timestamp: datetime,
        divergence_threshold: Decimal = Decimal("2.0"),
    ) -> RelativeStrengthResult:
        """Calculate relative strength of symbol vs base asset.

        Args:
            symbol_start_price: Symbol price at reference point
            symbol_current_price: Symbol current price
            base_start_price: Base asset price at reference point
            base_current_price: Base asset current price
            timestamp: Timestamp for this calculation
            divergence_threshold: Threshold for divergence detection (%)

        Returns:
            RelativeStrengthResult with detailed analysis

        Example:
            >>> rs = RelativeStrengthAnalyzer.calculate_relative_strength(
            ...     symbol_start_price=Decimal("3000"),
            ...     symbol_current_price=Decimal("3200"),  # +6.67%
            ...     base_start_price=Decimal("90000"),
            ...     base_current_price=Decimal("91800"),  # +2%
            ...     timestamp=datetime.now(timezone.utc)
            ... )
            >>> print(f"RS: {rs.relative_strength}% ({rs.strength_category})")
        """
        # Calculate percentage changes
        symbol_change_pct = (
            (symbol_current_price - symbol_start_price) / symbol_start_price * 100
        )
        base_change_pct = (
            (base_current_price - base_start_price) / base_start_price * 100
        )

        # Relative strength = symbol change - base change
        relative_strength = symbol_change_pct - base_change_pct

        # Detect divergence
        divergence_type = RelativeStrengthAnalyzer._detect_divergence(
            symbol_change_pct, base_change_pct, divergence_threshold
        )

        return RelativeStrengthResult(
            timestamp=timestamp,
            symbol_change_pct=symbol_change_pct,
            base_change_pct=base_change_pct,
            relative_strength=relative_strength,
            divergence_type=divergence_type,
        )

    @staticmethod
    def _detect_divergence(
        symbol_change: Decimal,
        base_change: Decimal,
        threshold: Decimal,
    ) -> Literal["bullish", "bearish", "none"]:
        """Detect bullish/bearish divergence.

        Bullish divergence: Symbol up significantly, base flat/down
        Bearish divergence: Symbol down significantly, base flat/up
        """
        # Bullish divergence
        if symbol_change > threshold and base_change <= 1:
            return "bullish"

        # Bearish divergence
        if symbol_change < -threshold and base_change >= -1:
            return "bearish"

        return "none"

    @staticmethod
    def calculate_relative_strength_series(
        symbol_candles: Sequence[Candle],
        base_candles: Sequence[Candle],
        reference_index: int = 0,
        price_field: Literal["close", "open", "high", "low"] = "close",
        divergence_threshold: Decimal = Decimal("2.0"),
    ) -> list[RelativeStrengthResult]:
        """Calculate relative strength series over time (series-first).

        Args:
            symbol_candles: Candles for symbol
            base_candles: Candles for base asset
            reference_index: Index of reference candle (default: 0 = first candle)
            price_field: Which price field to use
            divergence_threshold: Threshold for divergence detection

        Returns:
            List of RelativeStrengthResult for each period after reference

        Example:
            >>> rs_series = RelativeStrengthAnalyzer.calculate_relative_strength_series(
            ...     eth_candles, btc_candles, reference_index=0
            ... )
            >>> for rs in rs_series[-10:]:  # Last 10 periods
            ...     print(f"{rs.timestamp}: {rs.relative_strength:+.2f}% ({rs.strength_category})")
        """
        # Align candles by timestamp
        ts_symbol = {c.timestamp: c for c in symbol_candles}
        ts_base = {c.timestamp: c for c in base_candles}
        common_ts = sorted(set(ts_symbol.keys()) & set(ts_base.keys()))

        if len(common_ts) < 2:
            raise ValueError("Need at least 2 common timestamps")

        if reference_index < 0 or reference_index >= len(common_ts):
            raise ValueError(
                f"reference_index must be in [0, {len(common_ts) - 1}]"
            )

        # Get reference prices
        reference_ts = common_ts[reference_index]
        symbol_ref_price = getattr(ts_symbol[reference_ts], price_field)
        base_ref_price = getattr(ts_base[reference_ts], price_field)

        # Calculate RS for each timestamp
        results = []
        for ts in common_ts[reference_index + 1 :]:  # Start after reference
            symbol_current = getattr(ts_symbol[ts], price_field)
            base_current = getattr(ts_base[ts], price_field)

            rs = RelativeStrengthAnalyzer.calculate_relative_strength(
                symbol_start_price=symbol_ref_price,
                symbol_current_price=symbol_current,
                base_start_price=base_ref_price,
                base_current_price=base_current,
                timestamp=ts,
                divergence_threshold=divergence_threshold,
            )

            results.append(rs)

        return results

    @staticmethod
    def rank_by_relative_strength(
        candles_dict: dict[str, Sequence[Candle]],
        base_candles: Sequence[Candle],
        reference_index: int = 0,
        price_field: Literal["close", "open", "high", "low"] = "close",
        top_n: int | None = None,
    ) -> list[tuple[str, RelativeStrengthResult]]:
        """Rank multiple symbols by relative strength vs base.

        Args:
            candles_dict: Dict of symbol -> candles
            base_candles: Base asset candles
            reference_index: Index of reference candle
            price_field: Which price field to use
            top_n: Return only top N (None = all)

        Returns:
            List of (symbol, RelativeStrengthResult) sorted by RS (descending)

        Example:
            >>> rankings = RelativeStrengthAnalyzer.rank_by_relative_strength(
            ...     {"ETH": eth_candles, "SOL": sol_candles, "BNB": bnb_candles},
            ...     btc_candles,
            ...     reference_index=0,
            ...     top_n=10
            ... )
            >>> for i, (symbol, rs) in enumerate(rankings, 1):
            ...     print(f"{i}. {symbol}: {rs.relative_strength:+.2f}%")
        """
        results = []

        for symbol, symbol_candles in candles_dict.items():
            try:
                rs_series = RelativeStrengthAnalyzer.calculate_relative_strength_series(
                    symbol_candles=symbol_candles,
                    base_candles=base_candles,
                    reference_index=reference_index,
                    price_field=price_field,
                )

                # Get latest RS
                if rs_series:
                    latest_rs = rs_series[-1]
                    results.append((symbol, latest_rs))
            except (ValueError, KeyError):
                # Skip symbols with errors (e.g., insufficient data)
                continue

        # Sort by relative strength (descending)
        results.sort(key=lambda x: x[1].relative_strength, reverse=True)

        if top_n is not None:
            results = results[:top_n]

        return results
