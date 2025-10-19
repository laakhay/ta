# Vision – Laakhay TA

Laakhay-TA will be the “PyTorch of technical analysis”: a lightweight, open toolkit where quants, builders, and educators compose indicators, arithmetic, and domain logic as easily as chaining tensors—yet keep full introspection and control for production systems.

## Guiding Principles

1. **Ergonomic surface, rock-solid core** – The public API should feel obvious (`ta.dataset(...)`, `ta.indicator(...)`, `sma_fast - sma_slow`) while the core stays stateless, type-safe, and battle-tested.
2. **Data-source agnostic** – CSVs, REST payloads, websockets, or in-memory arrays all normalize into immutable `Bar` and `OHLCVSeries` types—no hidden caches or global state.
3. **Composability everywhere** – Indicators, literals, arithmetic, logical nodes, and custom callables all participate in a shared expression graph that can be evaluated, serialized, or inspected.
4. **Declarative metadata** – Indicators self-describe their parameters, outputs, aliases, complexity, and docs so UIs, DSLs, and documentation stay in sync.
5. **Performance-optional** – Pure Python is the baseline; NumPy/Numba acceleration is a one-line opt-in that never changes behaviour or API shape.
6. **Transparency & diagnostics** – Availability windows, alignment rules, debug logs, and expression trees are first-class so users can trust every data point.

## Architectural Overview

| Layer | Responsibility | Key Components |
|-------|----------------|----------------|
| Core Data | Immutable series + alignment | `Bar`, `OHLCVSeries`, `Series` utilities |
| Execution Engine | Stateless graph evaluation | `Engine`, `SeriesOps`, `ExpressionNode` |
| Schema & Registry | Metadata & discovery | `indicator_registry`, `IndicatorSchema` |
| User API | Friendly builders & handles | `ta.dataset`, `ta.indicator`, `ta.pipeline`, `ta.literal` |
| Integrations | Streaming, strategy, export | `ta.stream`, `ta.strategy`, `ta.export` |

## Snapshot of the End Product

### 1. Loading Market Data

```python
import laakhay.ta as ta

btc = ta.load.csv("btc_1h.csv", symbol="BTCUSDT", timeframe="1h")
eth = ta.load.csv("eth_1h.csv", symbol="ETHUSDT", timeframe="1h")

dataset = ta.dataset(btc, eth)              # wraps internal TAInput
```

### 2. Indicator Handles & Introspection

```python
sma_fast = ta.indicator("sma", period=20)
sma_slow = ta.indicator("sma", period=50)
rsi      = ta.indicator("rsi", period=14)

output   = sma_fast(dataset)
print(output.series("BTCUSDT").last_value)

for param in sma_fast.schema.params:
    print(param.name, param.default, param.description)
```

### 3. Algebraic Composition

```python
bias   = ta.literal(15)
spread = sma_fast - sma_slow
combo  = (spread + bias) * rsi
signal = (combo > 100) & (rsi < 30)

result = signal(dataset)
print(result.series("BTCUSDT").last_value)    # boolean
print(signal.graph.describe())               # expression tree & dependencies
```

### 4. Declarative Pipelines

```python
pipe = (
    ta.pipeline(dataset)
      .indicator("ema_fast", "ema", period=12)
      .indicator("ema_slow", "ema", period=26)
      .expr("spread", "ema_fast - ema_slow")
      .literal("bias", 15)
      .expr("entry", "(spread + bias > 0) & (rsi < 30)")
)

outputs = pipe.run()
print(outputs["entry"].series("BTCUSDT").last_value)
```

### 5. Custom Indicator Registration

```python
@ta.register(name="my_custom")
def my_custom_indicator(ctx: ta.SeriesContext, period=21):
    bars = ctx.bars("BTCUSDT")
    values = ...  # compute numpy / pure python
    return ta.Series.from_pairs(bars.timestamps, values, meta={"period": period})

custom    = ta.indicator("my_custom", period=34)
composite = custom + sma_fast
print(composite.schema.description)
```

### 6. Streaming / Real-Time Updates

```python
stream = ta.stream(dataset.schema)           # builds stateful processor
stream.register(signal)

for bar in live_feed():
    update = stream.update(bar)
    if update.changed("signal", "BTCUSDT"):
        latest = update["signal"].series("BTCUSDT").last_value
        publish_alert_if_needed(latest)
```

### 7. Optional Acceleration

```python
ta.ensure_optional("numpy", extra="numpy")
accelerated = rsi(dataset)                   # automatically uses NumPy path
```

### 8. Strategy Scaffolding

```python
strategy = (
    ta.strategy.Builder(dataset)
      .indicator("ema_fast", "ema", period=12)
      .indicator("ema_slow", "ema", period=26)
      .indicator("rsi", "rsi", period=14)
      .rule("bullish_cross", lambda ctx: ctx["ema_fast"] > ctx["ema_slow"])
      .rule("rsi_support", lambda ctx: ctx["rsi"] < 30)
      .enter_long("long_entry", all_of=["bullish_cross", "rsi_support"])
      .exit_long("long_exit", lambda ctx: ctx["rsi"] > 65)
)

equity_curve = strategy.backtest(initial_capital=10_000)
equity_curve.plot()
```

## Alignment & Missing Data Philosophy

- All outputs are `Series` objects with explicit timestamps and `None` for missing values.
- Default policy aligns operands on timestamp intersection; missing values propagate.
- Users can override per expression or pipeline (`align("outer", fill="ffill")`, `coerce_missing(False)`).
- Diagnostics (`series.describe()`, `expression.graph.describe()`) highlight availability windows before deployment.

## Target Outcomes

- **Public adoption:** Developers reach for laakhay-ta first because simple use-cases are one-liners and advanced workflows don’t require leaving the library.
- **Backend decoupling:** The backend consumes laakhay-ta without custom forks, benefitting from community-driven improvements.
- **Ecosystem growth:** Schema metadata and expression graphs unlock AST engines, notebooks, GUIs, and language bindings.
- **Reliability:** Property-based tests, CI across pure/accelerated modes, and transparent diagnostics make it safe for mission-critical alerts or trading.

Laakhay-TA will deliver the flexibility of a domain-specific algebra with the robustness of a production-grade toolkit—making it the centerpiece of both internal systems and the broader technical analysis community.
