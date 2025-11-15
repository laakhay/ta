"""Dataset helpers shared across TA consumers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from ..core.bar import Bar
from ..core.dataset import SOURCE_LIQUIDATION, SOURCE_OHLCV, SOURCE_ORDERBOOK, SOURCE_TRADES, Dataset
from ..core.dataset import dataset as _dataset_builder
from ..core.ohlcv import OHLCV
from ..core.series import Series
from ..core.timestamps import coerce_timestamp

NUMERIC_FIELDS = {"open", "high", "low", "close", "volume"}


def dataset(*args: Any, **kwargs: Any) -> Dataset:
    """Backwards-compatible factory that proxies to core.dataset.dataset."""
    return _dataset_builder(*args, **kwargs)


def _normalize_bar_value(key: str, value: Any) -> Any:
    """Normalize individual bar field values."""
    if key == "timestamp":
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return value
        if isinstance(value, int | float):
            return datetime.fromtimestamp(float(value))
        return value

    if key in NUMERIC_FIELDS:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except (TypeError, ValueError):
                return value
        if isinstance(value, int | float):
            return float(value)
    return value


def dataset_from_bars(
    bars: Sequence[Mapping[str, Any]],
    *,
    symbol: str,
    timeframe: str,
) -> Dataset:
    """Create a Dataset from raw bar mappings."""
    if not bars:
        raise ValueError("bars sequence must not be empty")

    normalized = []
    for bar in bars:
        normalized.append({key: _normalize_bar_value(key, value) for key, value in bar.items()})

    sorted_bars = sorted(normalized, key=lambda item: item["timestamp"])
    ta_bars = [
        Bar.from_raw(
            ts=item["timestamp"],
            open=item["open"],
            high=item["high"],
            low=item["low"],
            close=item["close"],
            volume=item.get("volume", 0.0),
            is_closed=item.get("is_closed", True),
        )
        for item in sorted_bars
    ]

    ohlcv = OHLCV.from_bars(ta_bars, symbol=str(symbol), timeframe=str(timeframe))
    dataset_obj = Dataset()
    dataset_obj.add_series(symbol=str(symbol), timeframe=str(timeframe), series=ohlcv)
    return dataset_obj


def trim_dataset(dataset_obj: Dataset, *, symbol: str, timeframe: str, trim: int) -> Dataset:
    """Trim a dataset to account for indicator lookback requirements."""
    if trim <= 0:
        return dataset_obj

    series = dataset_obj.series(symbol, timeframe)
    if series is None:
        raise ValueError(f"Dataset missing series for {symbol} {timeframe}")

    try:
        trimmed = series[trim:]
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("Failed to trim dataset for indicator lookback") from exc

    if len(trimmed) == 0:
        raise ValueError("Not enough historical bars remain after applying lookback trim")

    dataset_obj.add_series(symbol=symbol, timeframe=timeframe, series=trimmed)
    return dataset_obj


def _normalize_timestamp(value: Any) -> datetime:
    """Normalize timestamp value to datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            raise ValueError(f"Invalid datetime string: {value}")
    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value))
    raise ValueError(f"Cannot normalize timestamp from type: {type(value)}")


def _normalize_numeric(value: Any) -> float:
    """Normalize numeric value to float."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Cannot convert string to float: {value}")
    if isinstance(value, int | float):
        return float(value)
    raise ValueError(f"Cannot normalize numeric from type: {type(value)}")


def _series_from_aggregations(
    aggregations: Sequence[Mapping[str, Any]],
    *,
    symbol: str,
    timeframe: str,
    field: str,
) -> Series[Any]:
    """Create a Series from aggregation data.

    Args:
        aggregations: Sequence of aggregation records with 'timestamp' and field value
        symbol: Trading pair symbol
        timeframe: Aggregation window
        field: Field name to extract from each aggregation

    Returns:
        Series with timestamps and field values
    """
    if not aggregations:
        raise ValueError(f"aggregations sequence must not be empty for field '{field}'")

    timestamps = []
    values = []

    for agg in aggregations:
        ts = _normalize_timestamp(agg["timestamp"])
        value = agg.get(field)
        if value is None:
            raise ValueError(f"Field '{field}' not found in aggregation record")
        timestamps.append(coerce_timestamp(ts))
        values.append(_normalize_numeric(value))

    return Series[Any](
        timestamps=tuple(timestamps),
        values=tuple(values),
        symbol=symbol,
        timeframe=timeframe,
    )


def dataset_from_multisource(
    *,
    symbol: str,
    timeframe: str,
    bars: Sequence[Mapping[str, Any]] | None = None,
    trades: Sequence[Mapping[str, Any]] | None = None,
    orderbooks: Sequence[Mapping[str, Any]] | None = None,
    liquidations: Sequence[Mapping[str, Any]] | None = None,
    exchange: str | None = None,
) -> Dataset:
    """Create a Dataset from multi-source normalized payloads.

    This function converts backend-normalized payloads (bars, trades, orderbooks,
    liquidations) into a Dataset instance that can be used for expression evaluation.

    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        timeframe: Primary timeframe for the dataset (e.g., '1h')
        bars: Optional sequence of OHLCV bar records. Each record should have:
              - timestamp: datetime or ISO string
              - open, high, low, close: numeric values
              - volume: numeric value (optional, defaults to 0.0)
              - is_closed: boolean (optional, defaults to True)
        trades: Optional sequence of trade aggregation records. Each record should have:
                - timestamp: datetime or ISO string
                - volume: total trade volume
                - count: number of trades
                - buy_volume: buy-side volume
                - sell_volume: sell-side volume
                - large_count: trades > $50k
                - whale_count: trades > $1M
                - avg_price: average trade price
                - vwap: volume-weighted average price
                - max_amount: largest trade amount (optional)
                - min_price: minimum trade price (optional)
        orderbooks: Optional sequence of order book snapshot records. Each record should have:
                    - timestamp: datetime or ISO string
                    - best_bid: best bid price
                    - best_ask: best ask price
                    - spread: bid-ask spread (absolute)
                    - spread_bps: spread in basis points
                    - mid_price: mid price
                    - bid_depth: total bid quantity
                    - ask_depth: total ask quantity
                    - imbalance: order book imbalance
                    - pressure: market pressure indicator
                    - large_liquidity: large order liquidity (optional)
        liquidations: Optional sequence of liquidation aggregation records. Each record should have:
                      - timestamp: datetime or ISO string
                      - count: number of liquidations
                      - volume: total liquidation volume
                      - value: total liquidation value (USDT)
                      - long_count: long liquidations (SELL side)
                      - short_count: short liquidations (BUY side)
                      - long_value: long liquidation value
                      - short_value: short liquidation value
                      - large_count: large liquidations (> $100k)
                      - large_value: large liquidation value
        exchange: Optional exchange identifier (e.g., 'binance', 'bybit')
                  Used to qualify source names for multi-exchange datasets

    Returns:
        Dataset instance with all provided sources added

    Raises:
        ValueError: If required fields are missing or data is invalid

    Example:
        >>> dataset = dataset_from_multisource(
        ...     symbol="BTCUSDT",
        ...     timeframe="1h",
        ...     bars=[{"timestamp": "2024-01-01T00:00:00Z", "open": 50000, ...}],
        ...     trades=[{"timestamp": "2024-01-01T00:00:00Z", "volume": 1000000, ...}],
        ...     exchange="binance"
        ... )
    """
    dataset_obj = Dataset()

    # Add OHLCV bars if provided
    if bars:
        ohlcv_dataset = dataset_from_bars(bars, symbol=symbol, timeframe=timeframe)
        # Extract OHLCV from the dataset and add with proper source
        ohlcv = ohlcv_dataset.series(symbol, timeframe)
        if ohlcv:
            source = SOURCE_OHLCV if not exchange else f"{SOURCE_OHLCV}_{exchange}"
            dataset_obj.add_series(symbol, timeframe, ohlcv, source=source)

    # Add trade aggregations if provided
    if trades:
        trade_fields = [
            "volume",
            "count",
            "buy_volume",
            "sell_volume",
            "large_count",
            "whale_count",
            "avg_price",
            "vwap",
        ]
        optional_trade_fields = ["max_amount", "min_price"]

        # Create series for each trade field
        # Note: For now, we create individual series. In the future, we might want
        # to create a TradeAggregation object that contains all fields.
        # For simplicity, we'll create a series for 'volume' as the primary field
        # and store others as separate series with qualified source names.
        volume_series = _series_from_aggregations(trades, symbol=symbol, timeframe=timeframe, field="volume")
        dataset_obj.add_trade_series(symbol, timeframe, volume_series, exchange=exchange)

        # Store other fields as separate series (this is a simplified approach)
        # In a full implementation, we might want a TradeAggregation type
        for field in trade_fields[1:] + optional_trade_fields:
            try:
                field_series = _series_from_aggregations(trades, symbol=symbol, timeframe=timeframe, field=field)
                source = f"{SOURCE_TRADES}_{field}" if not exchange else f"{SOURCE_TRADES}_{exchange}_{field}"
                dataset_obj.add_series(symbol, timeframe, field_series, source=source)
            except (ValueError, KeyError):
                # Skip optional fields that are missing
                if field in optional_trade_fields:
                    continue
                raise

    # Add order book snapshots if provided
    if orderbooks:
        orderbook_fields = [
            "best_bid",
            "best_ask",
            "spread",
            "spread_bps",
            "mid_price",
            "bid_depth",
            "ask_depth",
            "imbalance",
            "pressure",
        ]
        optional_orderbook_fields = ["large_liquidity"]

        # Create series for primary field (imbalance is commonly used)
        imbalance_series = _series_from_aggregations(orderbooks, symbol=symbol, timeframe=timeframe, field="imbalance")
        dataset_obj.add_orderbook_series(symbol, timeframe, imbalance_series, exchange=exchange)

        # Store other fields as separate series
        for field in orderbook_fields:
            if field == "imbalance":
                continue  # Already added
            try:
                field_series = _series_from_aggregations(orderbooks, symbol=symbol, timeframe=timeframe, field=field)
                source = f"{SOURCE_ORDERBOOK}_{field}" if not exchange else f"{SOURCE_ORDERBOOK}_{exchange}_{field}"
                dataset_obj.add_series(symbol, timeframe, field_series, source=source)
            except (ValueError, KeyError):
                raise

        # Optional fields
        for field in optional_orderbook_fields:
            try:
                field_series = _series_from_aggregations(orderbooks, symbol=symbol, timeframe=timeframe, field=field)
                source = f"{SOURCE_ORDERBOOK}_{field}" if not exchange else f"{SOURCE_ORDERBOOK}_{exchange}_{field}"
                dataset_obj.add_series(symbol, timeframe, field_series, source=source)
            except (ValueError, KeyError):
                continue

    # Add liquidation aggregations if provided
    if liquidations:
        liquidation_fields = [
            "count",
            "volume",
            "value",
            "long_count",
            "short_count",
            "long_value",
            "short_value",
            "large_count",
            "large_value",
        ]

        # Create series for primary field (value is commonly used)
        value_series = _series_from_aggregations(liquidations, symbol=symbol, timeframe=timeframe, field="value")
        dataset_obj.add_liquidation_series(symbol, timeframe, value_series, exchange=exchange)

        # Store other fields as separate series
        for field in liquidation_fields:
            if field == "value":
                continue  # Already added
            try:
                field_series = _series_from_aggregations(liquidations, symbol=symbol, timeframe=timeframe, field=field)
                source = f"{SOURCE_LIQUIDATION}_{field}" if not exchange else f"{SOURCE_LIQUIDATION}_{exchange}_{field}"
                dataset_obj.add_series(symbol, timeframe, field_series, source=source)
            except (ValueError, KeyError):
                raise

    if dataset_obj.is_empty:
        raise ValueError("At least one data source (bars, trades, orderbooks, or liquidations) must be provided")

    return dataset_obj
