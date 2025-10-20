"""Data loading utilities for CSV files."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from .core import OHLCV, Series
from .core.timestamps import coerce_timestamp
from .core.types import Price, Symbol, Timestamp


def from_csv(
    path: str | Path,
    symbol: Symbol,
    timeframe: str,
    source: str = "csv",
    timestamp_col: str = "timestamp",
    **col_mapping: str
) -> OHLCV | Series[Price]:
    """
    Load CSV file into OHLCV or Series.
    
    Args:
        path: Path to CSV file
        symbol: Trading symbol (e.g., "BTCUSDT")
        timeframe: Timeframe (e.g., "1h", "5m")
        source: Data source identifier
        timestamp_col: Name of timestamp column
        **col_mapping: Column name mappings
        
    Returns:
        OHLCV if OHLCV columns found, otherwise Series[Price]
        
    Column Mapping Examples:
        # For OHLCV data:
        csv("data.csv", "BTCUSDT", "1h", 
            open_col="open", high_col="high", low_col="low", 
            close_col="close", volume_col="volume", is_closed_col="closed")
            
        # For price series:
        csv("data.csv", "BTCUSDT", "1h", value_col="price")
        
        # For volume series:
        csv("data.csv", "BTCUSDT", "1h", value_col="volume")
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    # Default column mappings
    default_mapping = {
        "open_col": "open",
        "high_col": "high",
        "low_col": "low",
        "close_col": "close",
        "volume_col": "volume",
        "is_closed_col": "is_closed",
        "value_col": "value"
    }
    default_mapping.update(col_mapping)

    timestamps: list[Timestamp] = []
    opens: list[Price] = []
    highs: list[Price] = []
    lows: list[Price] = []
    closes: list[Price] = []
    volumes: list[Price] = []
    is_closed: list[bool] = []
    values: list[Price] = []

    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no headers")

        for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
            try:
                # Parse timestamp
                if timestamp_col not in row:
                    raise ValueError(f"Timestamp column '{timestamp_col}' not found in CSV")
                timestamp = coerce_timestamp(row[timestamp_col])
                timestamps.append(timestamp)

                # Check if we have OHLCV data
                ohlcv_cols = [
                    default_mapping["open_col"],
                    default_mapping["high_col"],
                    default_mapping["low_col"],
                    default_mapping["close_col"],
                    default_mapping["volume_col"]
                ]

                has_ohlcv = all(col in row for col in ohlcv_cols)

                if has_ohlcv:
                    # Parse OHLCV data
                    try:
                        opens.append(Decimal(str(row[default_mapping["open_col"]])))
                        highs.append(Decimal(str(row[default_mapping["high_col"]])))
                        lows.append(Decimal(str(row[default_mapping["low_col"]])))
                        closes.append(Decimal(str(row[default_mapping["close_col"]])))
                        volumes.append(Decimal(str(row[default_mapping["volume_col"]])))
                    except Exception as e:
                        raise ValueError(f"Invalid numeric data: {e}")

                    # Parse is_closed (default to True if not present)
                    is_closed_val = row.get(default_mapping["is_closed_col"], "true").lower()
                    is_closed.append(is_closed_val in ("true", "1", "yes", "closed"))
                else:
                    # Parse single value (Series)
                    if default_mapping["value_col"] not in row:
                        raise ValueError(f"Value column '{default_mapping['value_col']}' not found in CSV")
                    try:
                        values.append(Decimal(str(row[default_mapping["value_col"]])))
                    except Exception as e:
                        raise ValueError(f"Invalid numeric data: {e}")

            except (ValueError, KeyError) as e:
                raise ValueError(f"Error parsing row {row_num}: {e}")

    if not timestamps:
        raise ValueError("No valid data rows found in CSV")

    # Return OHLCV if we have OHLCV data, otherwise Series
    if opens:  # We have OHLCV data
        return OHLCV(
            timestamps=tuple(timestamps),
            opens=tuple(opens),
            highs=tuple(highs),
            lows=tuple(lows),
            closes=tuple(closes),
            volumes=tuple(volumes),
            is_closed=tuple(is_closed),
            symbol=symbol,
            timeframe=timeframe
        )
    else:  # We have Series data
        return Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol=symbol,
            timeframe=timeframe
        )
