# Python Package

Python ergonomics layer for the Rust-first TA engine.

## Scope

- User-facing Python APIs under `src/laakhay/`
- DSL and expression planning
- Test suite for Python behavior and Rust binding integration

## Layout

- `src/laakhay/` - package source
- `tests/` - Python tests
- `pyproject.toml` - packaging + tool config

## Local Commands

From repo root (preferred):

```bash
make lint-py
make test-py
```

From `python/` directly:

```bash
uv run --python 3.12 --with ruff ruff check src/laakhay/ tests/
uv run --python 3.12 --with pytest python -m pytest tests/ -q
```

## Packaging

- Built with maturin.
- Rust extension source: `../crates/ta-py/Cargo.toml`.
