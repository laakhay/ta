"""Open Interest data model."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpenInterest(BaseModel):
    """Open Interest data for futures contracts.
    
    Open Interest represents the total number of outstanding derivative contracts
    that have not been settled. It's a key indicator of market activity and liquidity.
    """

    symbol: str = Field(..., min_length=1, description="Trading symbol")
    timestamp: datetime = Field(..., description="Measurement timestamp (UTC)")
    open_interest: Decimal = Field(..., ge=0, description="Number of open contracts")
    open_interest_value: Optional[Decimal] = Field(
        default=None, ge=0, description="USDT value of open interest"
    )
    sum_open_interest: Optional[Decimal] = Field(
        default=None, ge=0, description="Alternative format: sum of open interest"
    )
    sum_open_interest_value: Optional[Decimal] = Field(
        default=None, ge=0, description="Alternative format: sum of open interest value"
    )

    @field_validator("open_interest")
    @classmethod
    def validate_open_interest(cls, v: Decimal) -> Decimal:
        """Validate open interest is non-negative."""
        if v < 0:
            raise ValueError("open_interest must be non-negative")
        return v

    @field_validator("open_interest_value", "sum_open_interest", "sum_open_interest_value")
    @classmethod
    def validate_optional_values(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate optional fields are non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("Value must be non-negative")
        return v

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    # --- Developer ergonomics ---

    @property
    def timestamp_ms(self) -> int:
        """Timestamp in milliseconds (Unix epoch)."""
        return int(self.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1000)

    def get_age_seconds(self) -> float:
        """Seconds since measurement timestamp."""
        now = datetime.now(timezone.utc)
        return max(0.0, (now - self.timestamp).total_seconds())

    def is_fresh(self, max_age_seconds: float = 120.0) -> bool:
        """Check if OI data is fresh (age < threshold)."""
        return self.get_age_seconds() < max_age_seconds
