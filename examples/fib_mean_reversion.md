# Fib Mean-Reversion Strategy Sketch

This note walks through how the finished swing/Fibonacci toolchain slots into
Laakhay-TA. Treat it as a wiring diagram for once the `swing_points` and
`fib_retracement` indicators (and any supporting strategy module) land.

## 1. Data hydration (multi-timeframe)

```python
from pathlib import Path
import laakhay.ta as ta

# Load 1h bars for execution + signal confirmation
one_hour = ta.io.csv.load_ohlcv(
    Path("data/BTCUSDT-1h.csv"),
    symbol="BTCUSDT",
    timeframe="1h",
)

# Load 4h bars for structural swings
four_hour = ta.io.csv.load_ohlcv(
    Path("data/BTCUSDT-4h.csv"),
    symbol="BTCUSDT",
    timeframe="4h",
)

dataset = ta.Dataset()
dataset.add_series("BTCUSDT", "1h", one_hour, source="ohlcv")
dataset.add_series("BTCUSDT", "4h", four_hour, source="ohlcv")
```

The pre-filled OHLC slots in `Dataset.build_context` (added during gap work)
ensure downstream indicators see `open/high/low/close/price` without extra
plumbing.

## 2. Indicator handles + expressions

When the swing/Fib indicators are available, the handles will expose the pieces
we need. The sketch below shows a directional mean-reversion setup:

```python
swing_4h = ta.indicator(
    "swing_points",
    left=2,
    right=2,
    return_mode="levels",  # returns {"swing_high", "swing_low"}
)

fib_levels = ta.indicator(
    "fib_retracement",
    levels=(0.382, 0.5, 0.618, 0.75),
)

rsi = ta.indicator("rsi", period=14)
```

Assume both indicators run on the 4h context while execution happens on 1h.

```python
swing_state = swing_4h(dataset.select(timeframe="4h"))
fib_state = fib_levels(dataset.select(timeframe="4h"))

down_levels = fib_state["down"]
level_618 = down_levels["0.618"]          # Series[Price] on 4h grid
level_50 = down_levels["0.5"]

# Align 4h anchors to 1h execution timeframe using the sync_timeframe primitive
reference_1h = dataset.select(timeframe="1h")["close"]
level_618_1h = ta.sync_timeframe(level_618, reference=reference_1h, fill="ffill")
level_50_1h = ta.sync_timeframe(level_50, reference=reference_1h, fill="ffill")

# Lay out retracement zone signals
close_price = ta.select(field="close")  # uses the new primitive helper

golden_entry = close_price.between(level_618_1h, level_50_1h)
invalidated = close_price > ta.sync_timeframe(down_levels["0.75"], reference=reference_1h, fill="ffill")

# Add a momentum filter to reinforce reversion context
oversold = rsi(dataset) < 35

long_signal = golden_entry & oversold & ~invalidated
```

At this point `long_signal` is an `Expression` thanks to operator overloading.
You can evaluate it in batch:

```python
engine = ta.Engine()
entry_flags = engine.evaluate(long_signal._node, dataset.to_context())
```

or schedule via the graph evaluator (`long_signal.run(dataset)`).

## 3. Strategy + backtest hook

Once a `ta.strategy` module exists (per roadmap), a backtest might look like:

```python
builder = ta.strategy.Builder(dataset)

strategy = (
    builder
    .entries(long_signal)
    .exits(invalidated | (rsi(dataset) > 55))
    .position_size("fixed_percent", value=0.02)
    .stop(loss_at=levels["0.75"])     # invalidation zone
    .target(take_profit_at=levels["0.382"])
    .build()
)

stats = strategy.backtest(initial_capital=10_000)
```

Until the formal strategy module lands, you can still export `entry_flags`,
`levels`, and raw prices to any external backtester. The immutable `Series`
objects contain timestamps, so wiring them into vectorised PnL calculators is
straightforward.

## 4. Streaming / live monitoring

For bar streaming:

1. Accumulate incoming 1h bars in a small ring buffer.
2. Every time a new 4h boundary closes, update the higher-timeframe OHLCV
   series and recompute `swing_points`.
3. Re-run `fib_retracement` to refresh levels and evaluate `long_signal` on the
   latest 1h bar(s).

Pseudocode stub:

```python
def on_bar(bar_1h):
    dataset.update_series("BTCUSDT", "1h", bar_1h)

    if bar_1h.timestamp aligns with 4h close:
        dataset.update_series("BTCUSDT", "4h", aggregate_last_4h())

    fib_state = fib_levels(dataset.select(timeframe="4h"))
    signal = long_signal.run(dataset)["BTCUSDT", "1h", "default"][-1]
    if signal:
        submit_order(...)
```

The new primitives (`select`, `rolling_argmax/min`) allow `swing_points` to
pinpoint structure without resorting to ad-hoc Series manipulation, keeping the
graph cache-friendly and alignable.

## 5. Dependencies

No extra libraries are required beyond Laakhay-TA for indicator composition.
For backtesting or order execution you can:

- Use the upcoming `ta.strategy` module (once merged).
- Plug outputs into an external engine (e.g., vectorbt, pandas-based testbed,
  or a lightweight custom simulator).
- Stream values into an exchange client; the framework’s immutable Series makes
  caching and invalidation manageable even in live loops.

Keep this document handy as the implementation lands—each section maps directly
to the primitives and indicators already queued in the roadmap.
