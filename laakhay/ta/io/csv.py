from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..core import OHLCV, Series
from ..core.timestamps import coerce_timestamp
from ..core.types import Price, Symbol, Timestamp


def from_csv(
    path: str | Path,
    symbol: Symbol,
    timeframe: str,
    source: str = "csv",
    timestamp_col: str = "timestamp",
    **col_mapping: str,
) -> OHLCV | Series[Price]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    default_mapping = {
        "open_col": "open",
        "high_col": "high",
        "low_col": "low",
        "close_col": "close",
        "volume_col": "volume",
        "is_closed_col": "is_closed",
        "value_col": "value",
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

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no headers")

        for row_num, row in enumerate(reader, start=2):
            try:
                if timestamp_col not in row:
                    raise ValueError(f"Timestamp column '{timestamp_col}' not found in CSV")
                timestamp = coerce_timestamp(row[timestamp_col])
                timestamps.append(timestamp)

                ohlcv_cols = [
                    default_mapping["open_col"],
                    default_mapping["high_col"],
                    default_mapping["low_col"],
                    default_mapping["close_col"],
                    default_mapping["volume_col"],
                ]

                has_ohlcv = all(col in row for col in ohlcv_cols)

                if has_ohlcv:
                    try:
                        opens.append(Decimal(str(row[default_mapping["open_col"]])))
                        highs.append(Decimal(str(row[default_mapping["high_col"]])))
                        lows.append(Decimal(str(row[default_mapping["low_col"]])))
                        closes.append(Decimal(str(row[default_mapping["close_col"]])))
                        volumes.append(Decimal(str(row[default_mapping["volume_col"]])))
                    except Exception as e:
                        raise ValueError(f"Invalid numeric data: {e}")

                    is_closed_val = row.get(default_mapping["is_closed_col"], "true").lower()
                    is_closed.append(is_closed_val in ("true", "1", "yes", "closed"))
                else:
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

    if opens:
        return OHLCV(
            timestamps=tuple(timestamps),
            opens=tuple(opens),
            highs=tuple(highs),
            lows=tuple(lows),
            closes=tuple(closes),
            volumes=tuple(volumes),
            is_closed=tuple(is_closed),
            symbol=symbol,
            timeframe=timeframe,
        )
    else:
        return Series[Price](
            timestamps=tuple(timestamps),
            values=tuple(values),
            symbol=symbol,
            timeframe=timeframe,
        )


def to_csv(
    data: OHLCV | Series[Any],
    path: str | Path,
    timestamp_col: str = "timestamp",
    **col_mapping: str,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    default_mapping = {
        "open_col": "open",
        "high_col": "high",
        "low_col": "low",
        "close_col": "close",
        "volume_col": "volume",
        "is_closed_col": "is_closed",
        "value_col": "value",
    }
    default_mapping.update(col_mapping)

    with path.open("w", newline="", encoding="utf-8") as f:
        if isinstance(data, OHLCV):
            fieldnames = [
                timestamp_col,
                default_mapping["open_col"],
                default_mapping["high_col"],
                default_mapping["low_col"],
                default_mapping["close_col"],
                default_mapping["volume_col"],
                default_mapping["is_closed_col"],
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i in range(len(data)):
                writer.writerow(
                    {
                        timestamp_col: data.timestamps[i].isoformat(),
                        default_mapping["open_col"]: str(data.opens[i]),
                        default_mapping["high_col"]: str(data.highs[i]),
                        default_mapping["low_col"]: str(data.lows[i]),
                        default_mapping["close_col"]: str(data.closes[i]),
                        default_mapping["volume_col"]: str(data.volumes[i]),
                        default_mapping["is_closed_col"]: data.is_closed[i],
                    }
                )
        else:
            fieldnames = [timestamp_col, default_mapping["value_col"]]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i in range(len(data)):
                writer.writerow(
                    {
                        timestamp_col: data.timestamps[i].isoformat(),
                        default_mapping["value_col"]: str(data.values[i]),
                    }
                )
