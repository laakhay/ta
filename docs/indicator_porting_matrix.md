# Indicator Porting Matrix (Python -> Rust)

This matrix tracks compute ownership for the public Python catalog.

Status meanings:
- `rust_native`: indicator compute is implemented directly in `ta-engine` and exposed in `ta_py`.
- `rust_via_primitives`: indicator compute is composed from Rust-backed primitives.
- `python_compute`: indicator compute still executes in Python and must be ported.
- `blocked`: known blocker prevents immediate Rust port.

## Current Status

| Indicator | Status |
| --- | --- |
| adx | rust_native |
| ao | rust_native |
| atr | rust_native |
| bb_lower | python_compute |
| bb_upper | python_compute |
| bbands | rust_native |
| cci | rust_native |
| cmf | rust_native |
| cmo | rust_native |
| coppock | python_compute |
| cross | python_compute |
| crossdown | python_compute |
| crossup | python_compute |
| donchian | python_compute |
| elder_ray | python_compute |
| ema | rust_via_primitives |
| enter | python_compute |
| exit | python_compute |
| falling | python_compute |
| falling_pct | python_compute |
| fib_anchor_high | python_compute |
| fib_anchor_low | python_compute |
| fib_level_down | python_compute |
| fib_level_up | python_compute |
| fib_retracement | python_compute |
| fisher | python_compute |
| hma | rust_via_primitives |
| ichimoku | python_compute |
| in_channel | python_compute |
| keltner | python_compute |
| klinger | python_compute |
| macd | rust_native |
| mfi | python_compute |
| obv | rust_native |
| out | python_compute |
| psar | python_compute |
| rising | python_compute |
| rising_pct | python_compute |
| roc | rust_native |
| rsi | rust_native |
| select | python_compute |
| sma | rust_via_primitives |
| stoch_d | python_compute |
| stoch_k | python_compute |
| stochastic | rust_native |
| supertrend | python_compute |
| swing_high_at | python_compute |
| swing_highs | python_compute |
| swing_low_at | python_compute |
| swing_lows | python_compute |
| swing_points | rust_native |
| vortex | python_compute |
| vwap | rust_native |
| williams_r | rust_native |
| wma | rust_via_primitives |

## Exit Criteria

Before merge of the full Rust-first migration:
1. `python_compute` count must reach `0`.
2. Each indicator must be either `rust_native` or `rust_via_primitives`.
3. Any temporary `blocked` item must include owner and unblock date.
