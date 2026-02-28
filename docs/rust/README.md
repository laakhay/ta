# TA Rust Workspace

Rust-first runtime workspace for `laakhay-ta`.

Crates:
- `ta-engine`: core runtime kernels and indicator math.
- `ta-ffi`: C ABI wrapper over `ta-engine`.
- `ta-py`: PyO3 bindings used by Python package.
- `ta-node` (scaffold): future Node bindings.

This workspace is the canonical implementation for runtime-heavy TA operations.
