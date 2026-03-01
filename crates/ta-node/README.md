# ta-node

Node bindings for direct `ta-engine` indicator calls.

## Status

Bootstrapped as a `napi-rs` addon crate. Direct indicator endpoints are added incrementally.

Current direct endpoints:
- `engineVersion`
- `sma`, `ema`, `wma`, `hma`
- `rsi`, `roc`, `cmo`
- `macd` (object output)
- `bbands` (object output)

## Principles

- Keep API surface thin over `ta-engine`.
- No planner/DSL in this crate.
- Keep validation strict and error messages stable.

## Development

```bash
cargo check -p ta-node
cargo test -p ta-node
```

Validation:
- Period parameters must be `> 0`.
- Invalid period returns `ERR_PERIOD_INVALID`.
