"""Mark Price and Index Price data model."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MarkPrice(BaseModel):
    """Mark Price and Index Price data for perpetual futures.

    Mark Price is used for liquidations and unrealized PnL calculations.
    Index Price is the weighted average spot price from multiple exchanges.

    These prices prevent market manipulation and unfair liquidations.
    """

    symbol: str = Field(..., min_length=1, description="Trading symbol")
    mark_price: Decimal = Field(..., gt=0, description="Mark price (used for liquidations)")
    index_price: Decimal | None = Field(
        default=None, gt=0, description="Index price (spot reference)"
    )
    estimated_settle_price: Decimal | None = Field(
        default=None, gt=0, description="Estimated settlement price"
    )
    last_funding_rate: Decimal | None = Field(
        default=None, description="Last applied funding rate"
    )
    next_funding_time: datetime | None = Field(
        default=None, description="Next funding time (UTC)"
    )
    timestamp: datetime = Field(..., description="Data timestamp (UTC)")

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    # --- Price Analysis Properties ---

    @property
    def mark_index_spread(self) -> Decimal | None:
        """Spread between mark and index price (mark - index)."""
        if self.index_price is None:
            return None
        return self.mark_price - self.index_price

    @property
    def mark_index_spread_bps(self) -> Decimal | None:
        """Spread in basis points (10000 * (mark - index) / index)."""
        if self.index_price is None or self.index_price == 0:
            return None
        spread = self.mark_price - self.index_price
        return (spread / self.index_price) * Decimal("10000")

    @property
    def mark_index_spread_percentage(self) -> Decimal | None:
        """Spread as percentage (100 * (mark - index) / index)."""
        if self.index_price is None or self.index_price == 0:
            return None
        spread = self.mark_price - self.index_price
        return (spread / self.index_price) * Decimal("100")

    @property
    def is_premium(self) -> bool | None:
        """True if mark price is above index (futures trading at premium)."""
        if self.mark_index_spread is None:
            return None
        return self.mark_index_spread > 0

    @property
    def is_discount(self) -> bool | None:
        """True if mark price is below index (futures trading at discount)."""
        if self.mark_index_spread is None:
            return None
        return self.mark_index_spread < 0

    @property
    def is_high_spread(self) -> bool:
        """Check if spread exceeds 30 bps threshold (0.30%)."""
        if self.mark_index_spread_bps is None:
            return False
        return abs(self.mark_index_spread_bps) > Decimal("30")

    @property
    def spread_severity(self) -> str:
        """Categorize spread severity: normal, moderate, high, extreme."""
        if self.mark_index_spread_bps is None:
            return "unknown"

        abs_spread = abs(self.mark_index_spread_bps)

        if abs_spread < 10:  # < 0.10%
            return "normal"
        elif abs_spread < 30:  # 0.10% - 0.30%
            return "moderate"
        elif abs_spread < 100:  # 0.30% - 1.00%
            return "high"
        else:  # > 1.00%
            return "extreme"

    # --- Time helpers ---

    @property
    def timestamp_ms(self) -> int:
        """Timestamp in milliseconds (Unix epoch)."""
        return int(self.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1000)

    def get_age_seconds(self) -> float:
        """Seconds since data timestamp."""
        now = datetime.now(timezone.utc)
        return max(0.0, (now - self.timestamp).total_seconds())

    def is_fresh(self, max_age_seconds: float = 5.0) -> bool:
        """Check if mark price data is fresh (age < threshold).

        Args:
            max_age_seconds: Maximum age threshold (default 5s for real-time data)

        Returns:
            True if age < threshold
        """
        return self.get_age_seconds() < max_age_seconds
