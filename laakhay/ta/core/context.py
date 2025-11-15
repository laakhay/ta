"""Source-specific context classes for multi-source expression evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..registry.models import SeriesContext
from .series import Series


@dataclass(frozen=True)
class OHLCVContext(SeriesContext):
    """Context for OHLCV (candlestick) data.

    Provides access to standard OHLCV fields:
    - price/close: Closing price
    - open: Opening price
    - high: Highest price
    - low: Lowest price
    - volume: Trading volume
    """

    price: Series[Any]
    close: Series[Any]
    open: Series[Any]
    high: Series[Any]
    low: Series[Any]
    volume: Series[Any]

    def __init__(self, **series: Series[Any]) -> None:
        """Initialize OHLCV context with required fields."""
        # Extract required fields, with fallbacks
        price = series.get("price") or series.get("close")
        close = series.get("close") or series.get("price")
        open_series = series.get("open")
        high = series.get("high")
        low = series.get("low")
        volume = series.get("volume")

        if not price or not close:
            raise ValueError("OHLCVContext requires 'price' or 'close' series")
        if not open_series:
            raise ValueError("OHLCVContext requires 'open' series")
        if not high:
            raise ValueError("OHLCVContext requires 'high' series")
        if not low:
            raise ValueError("OHLCVContext requires 'low' series")
        if not volume:
            raise ValueError("OHLCVContext requires 'volume' series")

        # Initialize parent with all series
        super().__init__(
            price=price,
            close=close,
            open=open_series,
            high=high,
            low=low,
            volume=volume,
        )


@dataclass(frozen=True)
class TradeContext(SeriesContext):
    """Context for trade data aggregations.

    Provides access to trade aggregation fields:
    - volume: Total trade volume
    - count: Number of trades
    - buy_volume: Buy-side volume (taker buys)
    - sell_volume: Sell-side volume (taker sells)
    - large_count: Trades > $50k
    - whale_count: Trades > $1M
    - avg_price: Average trade price
    - vwap: Volume-weighted average price
    - max_amount: Largest trade amount
    - min_price: Minimum trade price
    """

    volume: Series[Any]
    count: Series[Any]
    buy_volume: Series[Any]
    sell_volume: Series[Any]
    large_count: Series[Any]
    whale_count: Series[Any]
    avg_price: Series[Any]
    vwap: Series[Any]
    max_amount: Series[Any] | None = None
    min_price: Series[Any] | None = None

    def __init__(self, **series: Series[Any]) -> None:
        """Initialize TradeContext with required fields."""
        # Required fields
        volume = series.get("volume")
        count = series.get("count")
        buy_volume = series.get("buy_volume")
        sell_volume = series.get("sell_volume")
        large_count = series.get("large_count")
        whale_count = series.get("whale_count")
        avg_price = series.get("avg_price")
        vwap = series.get("vwap")

        if not volume:
            raise ValueError("TradeContext requires 'volume' series")
        if count is None:
            raise ValueError("TradeContext requires 'count' series")
        if not buy_volume:
            raise ValueError("TradeContext requires 'buy_volume' series")
        if not sell_volume:
            raise ValueError("TradeContext requires 'sell_volume' series")
        if large_count is None:
            raise ValueError("TradeContext requires 'large_count' series")
        if whale_count is None:
            raise ValueError("TradeContext requires 'whale_count' series")
        if not avg_price:
            raise ValueError("TradeContext requires 'avg_price' series")
        if not vwap:
            raise ValueError("TradeContext requires 'vwap' series")

        # Optional fields
        max_amount = series.get("max_amount")
        min_price = series.get("min_price")

        # Initialize parent with all series
        super().__init__(
            volume=volume,
            count=count,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            large_count=large_count,
            whale_count=whale_count,
            avg_price=avg_price,
            vwap=vwap,
            max_amount=max_amount,
            min_price=min_price,
        )


@dataclass(frozen=True)
class OrderBookContext(SeriesContext):
    """Context for order book snapshot data.

    Provides access to order book fields:
    - best_bid: Best bid price
    - best_ask: Best ask price
    - spread: Bid-ask spread (absolute)
    - spread_bps: Spread in basis points
    - mid_price: Mid price (bid + ask) / 2
    - bid_depth: Total bid quantity (sum of all levels)
    - ask_depth: Total ask quantity
    - imbalance: Order book imbalance: (bid_depth - ask_depth) / (bid_depth + ask_depth)
    - pressure: Market pressure indicator (-1 to 1)
    - large_liquidity: Large order liquidity
    """

    best_bid: Series[Any]
    best_ask: Series[Any]
    spread: Series[Any]
    spread_bps: Series[Any]
    mid_price: Series[Any]
    bid_depth: Series[Any]
    ask_depth: Series[Any]
    imbalance: Series[Any]
    pressure: Series[Any]
    large_liquidity: Series[Any] | None = None

    def __init__(self, **series: Series[Any]) -> None:
        """Initialize OrderBookContext with required fields."""
        # Required fields
        best_bid = series.get("best_bid")
        best_ask = series.get("best_ask")
        spread = series.get("spread")
        spread_bps = series.get("spread_bps")
        mid_price = series.get("mid_price")
        bid_depth = series.get("bid_depth")
        ask_depth = series.get("ask_depth")
        imbalance = series.get("imbalance")
        pressure = series.get("pressure")

        if not best_bid:
            raise ValueError("OrderBookContext requires 'best_bid' series")
        if not best_ask:
            raise ValueError("OrderBookContext requires 'best_ask' series")
        if spread is None:
            raise ValueError("OrderBookContext requires 'spread' series")
        if spread_bps is None:
            raise ValueError("OrderBookContext requires 'spread_bps' series")
        if not mid_price:
            raise ValueError("OrderBookContext requires 'mid_price' series")
        if not bid_depth:
            raise ValueError("OrderBookContext requires 'bid_depth' series")
        if not ask_depth:
            raise ValueError("OrderBookContext requires 'ask_depth' series")
        if imbalance is None:
            raise ValueError("OrderBookContext requires 'imbalance' series")
        if pressure is None:
            raise ValueError("OrderBookContext requires 'pressure' series")

        # Optional fields
        large_liquidity = series.get("large_liquidity")

        # Initialize parent with all series
        super().__init__(
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            spread_bps=spread_bps,
            mid_price=mid_price,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            imbalance=imbalance,
            pressure=pressure,
            large_liquidity=large_liquidity,
        )


@dataclass(frozen=True)
class LiquidationContext(SeriesContext):
    """Context for liquidation aggregation data.

    Provides access to liquidation fields:
    - count: Number of liquidations
    - volume: Total liquidation volume
    - value: Total liquidation value (USDT)
    - long_count: Long liquidations (SELL side)
    - short_count: Short liquidations (BUY side)
    - long_value: Long liquidation value
    - short_value: Short liquidation value
    - large_count: Large liquidations (> $100k)
    - large_value: Large liquidation value
    """

    count: Series[Any]
    volume: Series[Any]
    value: Series[Any]
    long_count: Series[Any]
    short_count: Series[Any]
    long_value: Series[Any]
    short_value: Series[Any]
    large_count: Series[Any]
    large_value: Series[Any]

    def __init__(self, **series: Series[Any]) -> None:
        """Initialize LiquidationContext with required fields."""
        # Required fields
        count = series.get("count")
        volume = series.get("volume")
        value = series.get("value")
        long_count = series.get("long_count")
        short_count = series.get("short_count")
        long_value = series.get("long_value")
        short_value = series.get("short_value")
        large_count = series.get("large_count")
        large_value = series.get("large_value")

        if count is None:
            raise ValueError("LiquidationContext requires 'count' series")
        if not volume:
            raise ValueError("LiquidationContext requires 'volume' series")
        if not value:
            raise ValueError("LiquidationContext requires 'value' series")
        if long_count is None:
            raise ValueError("LiquidationContext requires 'long_count' series")
        if short_count is None:
            raise ValueError("LiquidationContext requires 'short_count' series")
        if not long_value:
            raise ValueError("LiquidationContext requires 'long_value' series")
        if not short_value:
            raise ValueError("LiquidationContext requires 'short_value' series")
        if large_count is None:
            raise ValueError("LiquidationContext requires 'large_count' series")
        if not large_value:
            raise ValueError("LiquidationContext requires 'large_value' series")

        # Initialize parent with all series
        super().__init__(
            count=count,
            volume=volume,
            value=value,
            long_count=long_count,
            short_count=short_count,
            long_value=long_value,
            short_value=short_value,
            large_count=large_count,
            large_value=large_value,
        )


def create_context(source: str, **series: Series[Any]) -> SeriesContext:
    """Create appropriate context type based on source.

    Args:
        source: Source type ('ohlcv', 'trades', 'orderbook', 'liquidation')
        **series: Series data to populate the context

    Returns:
        Appropriate context class instance

    Raises:
        ValueError: If source is not recognized or required fields are missing
    """
    source_lower = source.lower()

    if source_lower == "ohlcv":
        return OHLCVContext(**series)
    elif source_lower == "trades":
        return TradeContext(**series)
    elif source_lower == "orderbook":
        return OrderBookContext(**series)
    elif source_lower == "liquidation":
        return LiquidationContext(**series)
    else:
        # Fallback to generic SeriesContext for unknown sources
        return SeriesContext(**series)
