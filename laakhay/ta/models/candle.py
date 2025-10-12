"""Candle (OHLCV) data model."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Candle(BaseModel):
    """OHLCV candle data.
    
    Immutable representation of a price bar with open, high, low, close, and volume.
    Designed to be data-source agnostic - any provider can produce Candle instances.
    """

    symbol: str = Field(..., min_length=1, description="Trading symbol (e.g., BTCUSDT)")
    timestamp: datetime = Field(..., description="Bar open time (UTC)")
    open: Decimal = Field(..., gt=0, description="Opening price")
    high: Decimal = Field(..., gt=0, description="Highest price")
    low: Decimal = Field(..., gt=0, description="Lowest price")
    close: Decimal = Field(..., gt=0, description="Closing price")
    volume: Decimal = Field(..., ge=0, description="Trading volume")
    is_closed: bool = Field(True, description="Whether the candle is closed/finalized")

    @field_validator("high")
    @classmethod
    def validate_high(cls, v: Decimal, info) -> Decimal:
        """Validate high >= low and high >= open, close."""
        if "low" in info.data and v < info.data["low"]:
            raise ValueError("high must be >= low")
        if "open" in info.data and v < info.data["open"]:
            raise ValueError("high must be >= open")
        if "close" in info.data and v < info.data["close"]:
            raise ValueError("high must be >= close")
        return v

    @field_validator("low")
    @classmethod
    def validate_low(cls, v: Decimal, info) -> Decimal:
        """Validate low <= high and low <= open, close."""
        if "high" in info.data and v > info.data["high"]:
            raise ValueError("low must be <= high")
        if "open" in info.data and v > info.data["open"]:
            raise ValueError("low must be <= open")
        if "close" in info.data and v > info.data["close"]:
            raise ValueError("low must be <= close")
        return v

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    # --- Developer ergonomics / freshness helpers ---
    
    @property
    def open_time_ms(self) -> int:
        """Get candle open time in milliseconds (Unix epoch)."""
        return int(self.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1000)

    def close_time_ms(self, interval_seconds: int = 60) -> int:
        """Approximate close time in ms given interval seconds (default 60s).

        For closed candles this equals open_time + interval; for streaming open
        candles the caller may pass the actual interval used.
        
        Args:
            interval_seconds: Candle interval in seconds (e.g., 60 for 1m, 3600 for 1h)
            
        Returns:
            Close time in milliseconds (Unix epoch)
        """
        return self.open_time_ms + (interval_seconds * 1000)

    def get_age_seconds(self, *, is_closed: bool = True, interval_seconds: int = 60) -> float:
        """Calculate how old this candle is in seconds.
        
        Args:
            is_closed: If True, age is measured from close_time; if False, from now
            interval_seconds: Candle interval in seconds
            
        Returns:
            Age in seconds (always non-negative)
        """
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        ref = self.close_time_ms(interval_seconds) if is_closed else now_ms
        return max(0.0, (now_ms - ref) / 1000.0)

    def is_fresh(
        self, 
        max_age_seconds: float = 120.0, 
        *, 
        is_closed: bool = True, 
        interval_seconds: int = 60
    ) -> bool:
        """Check if candle data is fresh (age below threshold).
        
        Args:
            max_age_seconds: Maximum age threshold in seconds
            is_closed: Whether to measure from close time or current time
            interval_seconds: Candle interval in seconds
            
        Returns:
            True if candle age < max_age_seconds
        """
        return self.get_age_seconds(is_closed=is_closed, interval_seconds=interval_seconds) < max_age_seconds

    # --- Common derived prices ---
    
    @property
    def hlc3(self) -> Decimal:
        """Typical price: (high + low + close) / 3"""
        return (self.high + self.low + self.close) / Decimal("3")
    
    @property
    def ohlc4(self) -> Decimal:
        """Average price: (open + high + low + close) / 4"""
        return (self.open + self.high + self.low + self.close) / Decimal("4")
    
    @property
    def hl2(self) -> Decimal:
        """Median price: (high + low) / 2"""
        return (self.high + self.low) / Decimal("2")
