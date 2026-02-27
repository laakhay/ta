# TA Node Bindings Plan

Chosen direction:
- Primary: `napi-rs` direct wrapper over `ta-engine`.
- Fallback: C-ABI bridge through `ta-ffi` if direct napi introduces portability issues.

Initial scope:
1. expose rolling + moving-average kernels
2. expose RSI/ATR/Stochastic/OBV/CMF
3. keep API data contract aligned with `ffi-contract-v1.md`
