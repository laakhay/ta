# Crates Workspace

Rust workspace crates for `laakhay-ta`.

## Crates

- `ta-engine` - core runtime and indicator compute kernels
- `ta-py` - Python bindings (PyO3) over `ta-engine`
- `ta-ffi` - C ABI wrapper over `ta-engine`
- `ta-node` - Node integration crate (currently minimal scaffold)

## Development

From repository root:

```bash
cargo check --workspace
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all --check
```

## Design Intent

- `ta-engine` stays dependency-light and deterministic.
- Adapter crates (`ta-py`, `ta-ffi`, `ta-node`) should be thin boundaries over engine capabilities.
