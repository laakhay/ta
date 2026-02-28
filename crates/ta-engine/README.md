# ta-engine

Core Rust execution engine for `laakhay-ta`.

## Responsibilities

- Dataset lifecycle and append/sync/downsample operations
- Indicator kernel implementations
- Batch plan execution
- Incremental execution runtime and state snapshot/restore
- Metadata catalog for supported indicators

## Source Layout

- `src/core/` - datasets, contracts, metadata, shared core types
- `src/indicators/` - indicator kernel modules (trend/momentum/volatility/volume/rolling)
- `src/execution/` - execution runtime (including incremental backend)

## Testing

```bash
cargo test -p ta-engine
```

## Notes

- Determinism and explicit contracts are preferred over implicit behavior.
- New compute logic should land here first, then be surfaced via adapters.
