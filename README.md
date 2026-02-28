# Laakhay TA

Rust-first technical analysis engine with a Python ergonomics layer.

## Status

- Beta and intentionally fast-moving.
- Breaking changes are expected.
- Priority is runtime speed, deterministic behavior, and clean architecture.

## Repository Layout

- `crates/ta-engine` - core Rust compute engine (dataset ops, indicators, execution runtime)
- `crates/ta-py` - PyO3 bindings exposing Rust runtime to Python
- `crates/ta-ffi` - C ABI surface for non-Python integrations
- `crates/ta-node` - Node-facing Rust crate scaffold
- `python/` - Python package (`laakhay-ta`), DSL/planner, tests, and tooling
- `tests/` - cross-runtime parity/golden-test scaffold (repo-level)
- `docs/` - architecture and reference docs

## Architecture (Current)

- Compute path is Rust-first.
- Python is primarily ergonomics: DSL, expression composition, planning, and package UX.
- Runtime-heavy indicator execution is handled by Rust kernels.

## Quick Start

### Prerequisites

- Rust toolchain (see `rust-toolchain.toml`)
- Python `3.12`
- `uv`

### Install dev environment

```bash
make install-dev
```

### Run checks

```bash
make format-check
make lint
make test
```

### Build Python wheel

```bash
make build
```

## Make Targets

Top-level targets run across the repository:

- `make format` / `make format-check`
- `make lint` / `make lint-fix`
- `make test` (`test-py` + `test-rs`)
- `make ci` (lint + format-check + test)

Useful scoped targets:

- `make lint-py`, `make lint-rs`
- `make test-py`, `make test-rs`
- `make check-rs`

## Python Package Notes

Python packaging lives in `python/pyproject.toml` and builds `ta_py` from `crates/ta-py` via maturin.

## Contribution Notes

- Keep commits small and logically scoped.
- Prefer moving compute/runtime logic into Rust.
- Avoid adding new Python fallbacks for already-ported Rust indicators.
