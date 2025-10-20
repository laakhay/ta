"""Data dumping utilities for CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Union

from .core import OHLCV, Series


def to_csv(
    data: Union[OHLCV, Series[Any]],
    path: Union[str, Path],
    timestamp_col: str = "timestamp",
    **col_mapping: str
) -> None:
    """
    Export OHLCV or Series to CSV file.
    
    Args:
        data: OHLCV or Series data to export
        path: Output CSV file path
        timestamp_col: Name of timestamp column
        **col_mapping: Column name mappings
        
    Column Mapping Examples:
        # For OHLCV data:
        csv(ohlcv, "output.csv", 
            open_col="open", high_col="high", low_col="low", 
            close_col="close", volume_col="volume", is_closed_col="closed")
            
        # For price series:
        csv(series, "output.csv", value_col="price")
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
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
    
    with path.open('w', newline='', encoding='utf-8') as f:
        if isinstance(data, OHLCV):
            # OHLCV data
            fieldnames = [
                timestamp_col,
                default_mapping["open_col"],
                default_mapping["high_col"],
                default_mapping["low_col"],
                default_mapping["close_col"],
                default_mapping["volume_col"],
                default_mapping["is_closed_col"]
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i in range(len(data)):
                writer.writerow({
                    timestamp_col: data.timestamps[i].isoformat(),
                    default_mapping["open_col"]: str(data.opens[i]),
                    default_mapping["high_col"]: str(data.highs[i]),
                    default_mapping["low_col"]: str(data.lows[i]),
                    default_mapping["close_col"]: str(data.closes[i]),
                    default_mapping["volume_col"]: str(data.volumes[i]),
                    default_mapping["is_closed_col"]: data.is_closed[i]
                })
        else:
            # Series data (since Union[OHLCV, Series[Any]], if not OHLCV, must be Series)
            fieldnames = [timestamp_col, default_mapping["value_col"]]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i in range(len(data)):
                writer.writerow({
                    timestamp_col: data.timestamps[i].isoformat(),
                    default_mapping["value_col"]: str(data.values[i])
                })
