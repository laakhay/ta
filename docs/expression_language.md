# Laakhay TA Expression Language

The Laakhay TA expression language is a powerful DSL for defining technical analysis strategies, indicators, and alerts. It supports algebraic composition of indicators, multi-source data access, and time-shifted queries.

## Basic Syntax

Expressions are composed of:
- **Indicators**: Functions like `sma(close, period=14)`
- **Operators**: Arithmetic (`+`, `-`, `*`, `/`) and Comparison (`>`, `<`, `==`, `&`, `|`)
- **Literals**: Numbers (`100`, `0.5`)
- **Source Fields**: Data access (`close`, `volume`, `BTC/USDT.price`)

## New Features: Aliases and Shorthands

To make expressions more concise and readable, we've introduced several aliases and syntactic sugars.

### Indicator Aliases

Common indicators have intuitive aliases:

| Alias | Canonical Name | Description |
|-------|----------------|-------------|
| `mean`, `average`, `avg` | `rolling_mean` | Rolling average over a window |
| `median`, `med` | `rolling_median` | Rolling median over a window |
| `std`, `stddev` | `rolling_std` | Rolling standard deviation over a window |
| `sum` | `rolling_sum` | Rolling sum over a window |
| `rma` | `rolling_rma` | Wilder's Rolling Moving Average (alpha=1/N) |
| `max` | `rolling_max` | Maximum value in a rolling window |
| `min` | `rolling_min` | Minimum value in a rolling window |
| `argmax` | `rolling_argmax` | Offset of maximum value in window |
| `argmin` | `rolling_argmin` | Offset of minimum value in window |
| `cumsum` | `cumulative_sum` | Cumulative sum of the series |
| `pos`, `positive` | `positive_values` | Replace negative values with 0 |
| `neg`, `negative` | `negative_values` | Replace positive values with 0 |
| `tr` | `true_range` | True Range (volatility of single bar) |

**Example:**
```python
# Equivalent expressions
expr1 = compile_expression("rolling_mean(close, period=20)")
expr2 = compile_expression("mean(close, period=20)")
```

### Parameter Aliases

Parameters also have aliases for clarity:

| Alias | Canonical Name | Description |
|-------|----------------|-------------|
| `lookback` | `period` | The size of the rolling window |

**Example:**
```python
# Equivalent expressions
expr1 = compile_expression("mean(close, period=20)")
expr2 = compile_expression("mean(close, lookback=20)")
```

### Field Shorthands

You can specify the input field as the first positional argument for most indicators. This is automatically detected if the argument is a field name or valid expression source.

**Example:**
```python
# Explicit field as keyword argument
expr1 = compile_expression("mean(period=20, field='volume')")

# Field shorthand (positional)
expr2 = compile_expression("mean(volume, lookback=20)")
```

This works for attributes and complex sources too:
```python
expr3 = compile_expression("mean(BTC.trades.volume, lookback=50)")
```

## Comparisons and Logic

Combine indicators with logical operators to create signals:

```python
# Price above 20-period moving average
signal = "close > mean(close, lookback=20)"

# Volume spike (volume > 2x average volume)
spike = "volume > 2 * mean(volume, lookback=20)"

# Trend confirmation (price > SMA50 AND price > SMA200)
uptrend = "(close > sma(close, period=50)) & (close > sma(close, period=200))"
```

## Time-Shifted Queries

Access past values using time suffixes:

```python
# Current price vs price 24 hours ago
change = "close > close.24h_ago"

# Indicator value 1 bar ago
crossover = "cross(fast_ma, slow_ma)"
```

## Validation

You can inspect the capabilities of any indicator using the registry:

```python
import laakhay.ta as ta

schema = ta.describe_indicator("rolling_mean")
print(schema.aliases)  # ['mean', 'average', 'avg']
print(schema.parameter_aliases)  # {'lookback': 'period'}
```
