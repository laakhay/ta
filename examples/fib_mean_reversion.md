# Fib Mean-Reversion Quick Reference

For a full walkthrough of swing detection, Fibonacci retracements, and multi-timeframe
alignment, see `examples/swing_fib_details.md`. This shorter note highlights the core
series you’ll compose inside Laakhay-TA when wiring mean-reversion strategies.

```python
import laakhay.ta as ta

# 1. Pull higher-timeframe context and compute structure.
swing = ta.indicator("swing_points", left=2, right=2, return_mode="levels")
fib = ta.indicator("fib_retracement", left=2, right=2, levels=(0.5, 0.618, 0.75))

dataset_4h = dataset.select(timeframe="4h")
swing_state = swing(dataset_4h)
fib_state = fib(dataset_4h)

# 2. Align retracement bands to the execution timeframe via ta.ref.
close_1h = ta.ref(dataset, timeframe="1h", field="close")
level_618 = ta.sync_timeframe(fib_state["down"]["0.618"], reference=close_1h, fill="ffill")
level_50 = ta.sync_timeframe(fib_state["down"]["0.5"], reference=close_1h, fill="ffill")
level_75 = ta.sync_timeframe(fib_state["down"]["0.75"], reference=close_1h, fill="ffill")

# 3. Compose the mean-reversion expression.
rsi = ta.indicator("rsi", period=14)
close_price = ta.select(field="close")
golden_entry = close_price.between(level_618, level_50)
invalidated = close_price > level_75
oversold = rsi(dataset.select(timeframe="1h")) < 35

long_signal = golden_entry & oversold & ~invalidated
```

Use the new `ta.ref` helper to slim down multi-timeframe boilerplate and the `Stream`
wrapper (`laakhay.ta.stream.Stream`) when incrementally feeding bars in a live or
backtesting runtime.

