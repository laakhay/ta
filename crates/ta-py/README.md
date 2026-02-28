# ta-py

PyO3 bindings crate for exposing `ta-engine` into Python.

## Purpose

- Bridge Python package calls to Rust runtime execution
- Convert Python inputs/outputs to engine contracts
- Keep Python-side compute fallback minimal

## Source Layout

- `src/api/` - Python-exposed entrypoints (dataset, indicators, execution)
- `src/conversions.rs` - value/type conversions
- `src/errors.rs` - Python error mapping
- `src/state.rs` - runtime/binding state management
- `src/lib.rs` - module wiring and exports

## Development

```bash
cargo test -p ta-py
```

For local Python install, use root `make install-dev`.
