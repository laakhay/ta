# Contributing to Laakhay-TA

## Setup
```bash
git clone https://github.com/laakhay/ta
cd ta
make install-dev
```

## Development Workflow
```bash
# all checks
make ci

# scoped checks
make lint-py
make lint-rs
make test-py
make test-rs
make format-check
```

## Architecture Expectations

- Rust-first compute: indicator/runtime logic should be implemented in `crates/ta-engine`.
- Python is an ergonomics layer: DSL/planner/API in `python/src/laakhay`.
- Avoid introducing new Python compute fallbacks for indicators already supported in Rust.
- Keep adapter crates thin (`ta-py`, `ta-ffi`, `ta-node`) and contract-focused.

## Expression System

The expression system supports multi-source data access, filtering, aggregation, and time-shifts:

- **Attribute chains**: `BTC/USDT.trades.volume`, `binance.BTC.orderbook.imbalance`
- **Filters**: `trades.filter(amount > 1_000_000).count`
- **Aggregations**: `trades.sum(amount)`, `trades.avg(price)`
- **Time-shifts**: `price.24h_ago`, `volume.change_pct_24h`

When adding new features:
- Update parser in `python/src/laakhay/ta/expr/dsl/parser.py` for new syntax
- Add AST nodes in `python/src/laakhay/ta/expr/dsl/nodes.py`
- Update compiler in `python/src/laakhay/ta/expr/dsl/compiler.py`
- Add expression models in `python/src/laakhay/ta/expr/algebra/models.py`
- Update planner in `python/src/laakhay/ta/expr/planner/planner.py` for requirement computation
- Update manifest in `python/src/laakhay/ta/expr/planner/manifest.py` if adding new sources/fields

## Commit Format
```
type(scope): description

feat(indicators): add MACD indicator
feat(expr): add filter and aggregation support
fix(series): handle empty series
refactor(planner): make manifest data-driven
docs: update README
```

Common scopes: `indicators`, `expr`, `planner`, `core`, `data`, `registry`

## PR Requirements

- Small, focused commits with clear intent.
- All CI-equivalent checks pass locally:
  - `make format-check`
  - `make lint`
  - `make test`
- Tests included/updated for behavior changes.
- For Rust indicator/runtime changes, parity coverage should be considered in Python parity tests.

## Getting Help
- [Issues](https://github.com/laakhay/ta/issues)
- laakhay.corp@gmail.com
