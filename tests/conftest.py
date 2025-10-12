"""Test configuration and fixtures."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from laakhay.ta.models import Candle


@pytest.fixture
def sample_candles():
    """Generate sample candles for testing."""
    def _make_candles(symbol: str, count: int = 50, base_price: float = 100.0):
        candles = []
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        
        for i in range(count):
            price = base_price + i
            candles.append(
                Candle(
                    symbol=symbol,
                    timestamp=base_time.replace(hour=i % 24, day=1 + i // 24),
                    open=Decimal(str(price)),
                    high=Decimal(str(price + 2)),
                    low=Decimal(str(price - 1)),
                    close=Decimal(str(price + 1)),
                    volume=Decimal("100.0"),
                    is_closed=True,
                )
            )
        return candles
    
    return _make_candles


@pytest.fixture
def sample_ohlc():
    """Generate OHLC tuples for testing."""
    def _make_ohlc(count: int = 50, base: float = 100.0):
        return [(base + i, base + i + 2, base + i - 1, base + i + 1) for i in range(count)]
    
    return _make_ohlc
