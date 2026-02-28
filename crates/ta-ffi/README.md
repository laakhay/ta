# ta-ffi

C ABI adapter for `ta-engine`.

## Purpose

Expose stable C-callable entry points so non-Rust runtimes can invoke engine functionality.

## Contract

- Header: `include/ta_engine.h`
- ABI version function: `ta_engine_abi_version()`

## Development

```bash
cargo test -p ta-ffi
```

Keep this crate as a thin translation layer over `ta-engine`.
