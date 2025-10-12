"""Funding Rate data model."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FundingRate(BaseModel):
    """Funding rate data for futures contracts.
    
    Funding rates are periodic payments between longs and shorts in perpetual futures.
    Positive rate = longs pay shorts (futures trading at premium).
    Negative rate = shorts pay longs (futures trading at discount).
    """

    symbol: str = Field(..., min_length=1, description="Trading symbol")
    funding_time: datetime = Field(..., description="Funding time (UTC)")
    funding_rate: Decimal = Field(..., description="Funding rate (decimal, not percentage)")
    mark_price: Optional[Decimal] = Field(
        default=None, 
        gt=0, 
        description="Mark price at funding time"
    )
    
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    # --- Developer ergonomics ---

    @property
    def funding_time_ms(self) -> int:
        """Funding time in milliseconds (Unix epoch)."""
        return int(self.funding_time.replace(tzinfo=timezone.utc).timestamp() * 1000)

    @property
    def funding_rate_percentage(self) -> Decimal:
        """Funding rate as percentage (multiply by 100)."""
        return self.funding_rate * Decimal("100")

    @property
    def annual_rate_percentage(self) -> Decimal:
        """Estimated annual rate percentage.
        
        Assumes funding every 8 hours = 3x per day = 1095x per year.
        """
        return self.funding_rate_percentage * Decimal("1095")

    @property
    def is_positive(self) -> bool:
        """True if funding rate is positive (longs pay shorts)."""
        return self.funding_rate > 0

    @property
    def is_negative(self) -> bool:
        """True if funding rate is negative (shorts pay longs)."""
        return self.funding_rate < 0

    @property
    def is_high(self) -> bool:
        """True if absolute funding rate > 0.01% (high funding pressure)."""
        return abs(self.funding_rate_percentage) > Decimal("0.01")

    def get_age_seconds(self, now_ms: Optional[int] = None) -> float:
        """Seconds since funding time.
        
        Args:
            now_ms: Optional current time in milliseconds. If None, uses current time.
            
        Returns:
            Age in seconds (always non-negative)
        """
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return max(0.0, (now_ms - self.funding_time_ms) / 1000.0)

    def is_fresh(self, max_age_seconds: float = 300.0) -> bool:
        """Check if funding rate is fresh (age < threshold).
        
        Args:
            max_age_seconds: Maximum age threshold (default 300s = 5min)
            
        Returns:
            True if age < threshold
        """
        return self.get_age_seconds() < max_age_seconds
