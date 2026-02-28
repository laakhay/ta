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
| bb_lower | rust_via_primitives |
| bb_upper | rust_via_primitives |
| bbands | rust_native |
| cci | rust_native |
| cmf | rust_native |
| cmo | rust_native |
| coppock | rust_native |
| cross | rust_native |
| crossdown | rust_native |
| crossup | rust_native |
| donchian | rust_native |
| elder_ray | rust_native |
| ema | rust_via_primitives |
| enter | rust_native |
| exit | rust_native |
| falling | rust_native |
| falling_pct | rust_native |
| fib_anchor_high | rust_via_primitives |
| fib_anchor_low | rust_via_primitives |
| fib_level_down | rust_via_primitives |
| fib_level_up | rust_via_primitives |
| fib_retracement | rust_via_primitives |
| fisher | rust_native |
| hma | rust_via_primitives |
| ichimoku | rust_native |
| in_channel | rust_native |
| keltner | rust_native |
| klinger | rust_native |
| macd | rust_native |
| mfi | rust_native |
| obv | rust_native |
| out | rust_native |
| psar | rust_native |
| rising | rust_native |
| rising_pct | rust_native |
| roc | rust_native |
| rsi | rust_native |
| select | rust_via_primitives |
| sma | rust_via_primitives |
| stoch_d | rust_via_primitives |
| stoch_k | rust_via_primitives |
| stochastic | rust_native |
| supertrend | rust_native |
| swing_high_at | rust_via_primitives |
| swing_highs | rust_via_primitives |
| swing_low_at | rust_via_primitives |
| swing_lows | rust_via_primitives |
| swing_points | rust_native |
| vortex | rust_native |
| vwap | rust_native |
| williams_r | rust_native |
| wma | rust_via_primitives |

## Exit Criteria

Before merge of the full Rust-first migration:
1. `python_compute` count must reach `0`.
2. Each indicator must be either `rust_native` or `rust_via_primitives`.
3. Any temporary `blocked` item must include owner and unblock date.
