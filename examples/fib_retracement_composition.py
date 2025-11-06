"""Compose Fibonacci retracement levels inside an expression workflow."""

from __future__ import annotations

from pathlib import Path

import laakhay.ta as ta


def load_datasets() -> ta.Dataset:
    """Load 4h swing context and 1h execution context into a single dataset."""
    dataset = ta.Dataset()

    one_hour = ta.io.csv.load_ohlcv(
        Path("data/BTCUSDT-1h.csv"),
        symbol="BTCUSDT",
        timeframe="1h",
    )
    four_hour = ta.io.csv.load_ohlcv(
        Path("data/BTCUSDT-4h.csv"),
        symbol="BTCUSDT",
        timeframe="4h",
    )

    dataset.add_series("BTCUSDT", "1h", one_hour, source="ohlcv")
    dataset.add_series("BTCUSDT", "4h", four_hour, source="ohlcv")
    return dataset


def fib_618_band(dataset: ta.Dataset) -> ta.Series[ta.Price]:
    """
    Build a 0.618 retracement band aligned to the 1h timeframe.

    Steps:
    1. Detect swing highs/lows on the 4h context.
    2. Compute Fibonacci retracement levels (including 0.618) on the same timeframe.
    3. Sync the 4h retracement line down to the 1h execution grid.
    """
    swing = ta.indicator("swing_points", left=2, right=2, return_mode="levels")
    fib = ta.indicator("fib_retracement", left=2, right=2, levels=(0.618,), mode="down")

    # Slice out the 4h view for structural calculations.
    dataset_4h = dataset.select(timeframe="4h")
    swing_state = swing(dataset_4h)
    fib_state = fib(dataset_4h)

    # Extract the downward 0.618 level (Series on 4h timestamps).
    level_618_4h = fib_state["down"]["0.618"]

    # Sync the 4h retracement down to 1h using the built-in primitive.
    close_1h = dataset.select(timeframe="1h")["close"]
    level_618_1h = ta.sync_timeframe(level_618_4h, reference=close_1h, fill="ffill")

    return level_618_1h


def build_signal(dataset: ta.Dataset) -> ta.Expression:
    """
    Compose a mean-reversion entry signal using the 0.618 band.

    Signal logic:
    - price trades between the 0.618 and 0.5 retracements
    - RSI confirms momentum exhaustion
    - invalidate when price closes above the 0.75 retracement
    """
    swing = ta.indicator("swing_points", left=2, right=2, return_mode="levels")
    fib = ta.indicator("fib_retracement", left=2, right=2, levels=(0.5, 0.618, 0.75), mode="down")

    dataset_4h = dataset.select(timeframe="4h")
    fib_state = fib(dataset_4h)
    close_1h = dataset.select(timeframe="1h")["close"]

    # Sync each retracement to the 1h execution timeframe.
    level_618 = ta.sync_timeframe(fib_state["down"]["0.618"], reference=close_1h, fill="ffill")
    level_50 = ta.sync_timeframe(fib_state["down"]["0.5"], reference=close_1h, fill="ffill")
    level_75 = ta.sync_timeframe(fib_state["down"]["0.75"], reference=close_1h, fill="ffill")

    # Core price series on 1h bars.
    close_price = ta.select(field="close")

    golden_entry = close_price.between(level_618, level_50)
    invalidated = close_price > level_75

    rsi = ta.indicator("rsi", period=14)
    oversold = rsi(dataset.select(timeframe="1h")) < 35

    return golden_entry & oversold & ~invalidated


def main() -> None:
    dataset = load_datasets()
    level_618 = fib_618_band(dataset)

    # Evaluate the latest retracement value on the 1h grid.
    print("Latest 0.618 level:", level_618.values[-1], "@", level_618.timestamps[-1])

    signal_expr = build_signal(dataset)
    signal_series = signal_expr.run(dataset)
    latest_signal = signal_series[("BTCUSDT", "1h", "default")].values[-1]
    print("Latest signal flag:", latest_signal)


if __name__ == "__main__":
    main()

