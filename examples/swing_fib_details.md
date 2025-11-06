# Swing Structure & Fibonacci Toolkit

This note explains how the `swing_points` and `fib_retracement` indicators work,
why they return the shapes they do, and how to combine them in expressions.

## 1. Swing Points – Detecting Local Extremes

```python
from laakhay.ta.indicators.pattern import swing_points
```

### Parameters
- `left`, `right` – number of bars on either side that must be strictly lower (for highs) or
  higher (for lows). Defaults: `left=2`, `right=2` (classic “fractals”).
- `return_mode` – `"flags"` (default) or `"levels"`.
  - `"flags"` ⇒ boolean series marking swing candles.
  - `"levels"` ⇒ full-price series with availability masks identifying the swing points.

### Algorithm (stateless)
1. Validate that `high` and `low` series exist and share metadata.
2. For each index `i` with enough context (`left <= i < len - right`):
   - Inspect the window `[i-left : i+right]`.
   - Set `swing_high[i] = True` if the current high is the unique maximum.
   - Set `swing_low[i] = True` if the current low is the unique minimum.
3. Fill availability masks so consumers know which indices were evaluated.

### Return Value
```python
{
    "swing_high": Series[bool] or Series[Price],
    "swing_low": Series[bool] or Series[Price],
}
```
- Both series retain the original timestamps/timeframe.
- Availability masks ensure downstream operators only consider confirmed swings.
- No state is retained; every call recomputes from the provided series.

### Example
```python
dataset_4h = dataset.select(timeframe="4h")
swings = swing_points(dataset_4h, left=2, right=2, return_mode="levels")

swing_high_prices = swings["swing_high"]
swing_low_prices = swings["swing_low"]

# Check candles where a high swing was confirmed
confirmed_highs = [
    (ts, price)
    for (ts, price), mask in zip(swing_high_prices, swing_high_prices.availability_mask, strict=False)
    if mask
]
```

## 2. Fibonacci Retracement – Projecting Levels from Swings

```python
from laakhay.ta.indicators.pattern import fib_retracement
```

### Parameters
- `left`, `right` – passed to the internal swing detector (defaults mirror `swing_points`).
- `levels` – tuple of Fibonacci ratios (`(0.382, 0.5, 0.618, ...)`).
- `mode` – `"down"` (retracement after an up move), `"up"` (retracement after a down move),
  or `"both"` (default).

### Algorithm
1. Reuse `_compute_swings` to retrieve swing flags and availability masks.
2. Walk forward through the series, capturing the latest confirmed swing high/low.
3. Whenever both anchors exist and a valid move is detected:
   - Downward retracement: `high - (high - low) * level`.
   - Upward retracement: `low + (high - low) * level`.
4. Populate a `Series[Price]` per ratio/direction, broadcasting the latest value between
   swing updates. Availability masks flip `True` only when the anchors are confirmed.

### Return Value
```python
{
    "anchor_high": Series[Price],
    "anchor_low": Series[Price],
    "down": {"0.618": Series[Price], ...},
    "up":   {"0.618": Series[Price], ...},
}
```
- All outputs are immutable `Series` to keep alignment with the expression system.
- Availability masks show when each level is active; otherwise the series is inert.
- The indicator is still stateless: given the same inputs, you receive identical outputs.

### Example
```python
dataset_4h = dataset.select(timeframe="4h")
fib = fib_retracement(dataset_4h, levels=(0.5, 0.618, 0.75), mode="down")

anchor_high = fib["anchor_high"]
level_618 = fib["down"]["0.618"]

# Latest 0.618 value and timestamp
latest_level = level_618.values[-1]
latest_ts = level_618.timestamps[-1]
```

## 3. Aligning Levels to Execution Timeframes

Retracement lines live on the timeframe where swings are computed (typically higher).
To test entries on a lower timeframe, use the existing `sync_timeframe` primitive.

```python
close_1h = dataset.select(timeframe="1h")["close"]
level_618_1h = ta.sync_timeframe(level_618, reference=close_1h, fill="ffill")
```

The `ta.ref` helper wraps both selection and optional syncing:

```python
level_618_1h = ta.ref(
    dataset,
    timeframe="4h",
    field="close",
    symbol="BTCUSDT",
    reference=("BTCUSDT", "1h", "close"),
)
```

The combination of stateless series + availability masks + `sync_timeframe` keeps
the workflow entirely functional and expression-friendly.

For bulk aggregation (e.g., preparing a higher-timeframe dataset once), the
`ta.resample` helper wraps the `downsample` primitive and handles timeframe math:

```python
ohlc_4h = ta.resample(dataset, from_timeframe="1h", to_timeframe="4h", field="ohlcv")
```

### Why a “single level” is still a Series
- **Re-evaluated on every bar**: the indicator walks through the price series in
  timestamp order. For each bar it checks “do I have a confirmed swing high and
  low yet?” If yes, it computes the level for *this* bar; if no, it keeps the
  most recent value (or the raw anchor price before confirmation). In practice
  the number may stay constant for several bars, but the evaluation happens at
  each step.
- **Metadata preservation**: by emitting a `Series` that spans the same timestamps
  as the input, we retain `symbol`/`timeframe` and enable alignment with other
  indicators. Returning a scalar or ragged array would break the expression
  engine’s expectations (alignment, caching, broadcasting).
- **Availability semantics**: the level’s `availability_mask` is `False` until
  both anchors exist *and* the lookback window has passed confirmation (i.e.,
  left/right bars satisfied). Consumers can safely treat any `False` row as “not
  ready yet,” regardless of the numeric value being repeated.
- **Consistency with the rest of TA**: moving averages, rolling highs, and other
  indicators also emit series whose values often change slowly relative to the
  window size. It’s the same idea—series-based outputs are a natural fit for
  vectorised, functional composition.
- **Practical benefit**: because the level is just another `Series`, you can:
  - feed it to `sync_timeframe` to downsample or upsample automatically;
  - compare it directly against the execution price (`close > level_618`);
  - plot it alongside price data without extra transformation;
  - cache it in the graph evaluator, avoiding recomputation on every backtest run.

## 4. Putting It Together – Mean Reversion Signal

```python
swing = ta.indicator("swing_points", left=2, right=2, return_mode="levels")
fib = ta.indicator("fib_retracement", left=2, right=2, levels=(0.5, 0.618, 0.75))
rsi = ta.indicator("rsi", period=14)

dataset_4h = dataset.select(timeframe="4h")
fib_state = fib(dataset_4h)

close_1h = dataset.select(timeframe="1h")["close"]
level_618 = ta.sync_timeframe(fib_state["down"]["0.618"], reference=close_1h, fill="ffill")
level_50  = ta.sync_timeframe(fib_state["down"]["0.5"], reference=close_1h, fill="ffill")
level_75  = ta.sync_timeframe(fib_state["down"]["0.75"], reference=close_1h, fill="ffill")

close_price = ta.select(field="close")
golden_entry = close_price.between(level_618, level_50)
invalidated  = close_price > level_75
oversold     = rsi(dataset.select(timeframe="1h")) < 35

long_signal = golden_entry & oversold & ~invalidated
```

This `long_signal` can be evaluated or fed into the upcoming strategy module
exactly like any other expression, with thanks to the stateless, alignable
Series returned by both indicators.

## 5. Key Takeaways

- **Stateless**: Indicators do not keep internal caches; they derive everything from inputs.
- **Series-based**: Even single levels are broadcast as `Series`, enabling caching,
  alignment, and composition without additional adapters.
- **Availability masks**: Downstream consumers should respect `availability_mask`
  to know when a swing or level is valid.
- **Composability**: Once synced to the execution timeframe, the retracement levels
  drop into any comparison, logical combination, or strategy evaluation you need.
