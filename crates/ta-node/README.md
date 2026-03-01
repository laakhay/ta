# ta-node

Node bindings for direct `ta-engine` indicator calls.

## Status

Bootstrapped as a `napi-rs` addon crate. Direct indicator endpoints are added incrementally.

Current direct endpoints:
- `engineVersion`
- `sma`, `ema`, `rma`, `wma`, `hma`
- `rsi`, `roc`, `cmo`, `ao`, `coppock`, `williamsR`, `mfi`, `cci`
- `atr`, `atrFromTr`
- `obv`, `vwap`, `cmf`, `klingerVf`
- `macd`, `bbands`, `stochastic`, `adx`, `ichimoku`, `supertrend`, `psar`
- `swingPointsRaw`, `vortex`, `elderRay`, `fisher`, `donchian`, `keltner`, `klinger`

## Principles

- Keep API surface thin over `ta-engine`.
- No planner/DSL in this crate.
- Keep validation strict and error messages stable.

## Development

```bash
cargo check -p ta-node
cargo clippy -p ta-node --all-targets -- -D warnings
cargo test -p ta-node
```

Validation:
- Period parameters must be `> 0`.
- Invalid period returns `ERR_PERIOD_INVALID`.
- Mismatched series lengths return `ERR_LENGTH_MISMATCH`.

Parity harness:
- Fixture-driven parity checks live in `test/fixtures/parity_cases.json`.
- Tests compare wrapper outputs against direct `ta-engine` computations.
