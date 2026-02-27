# TA Rust-Core Modularization Plan (Aggressive Beta Track)

## Context
This is a beta library with near-zero external adoption. Optimize for speed, architecture quality, and long-term leverage, not backward-compatibility safety.

## Aggressive principles
1. Break APIs early when it simplifies the end-state.
2. Minimize dual-path maintenance (no long python-vs-rust coexistence).
3. Move runtime hot paths to Rust fast, then remove Python implementations.
4. Choose one packaging path early (`maturin` + PyO3) and commit.
5. Establish Rust crates as the source of truth, Python as binding surface.
6. Define Node/TS boundary early so we do not re-architect later.

## Target end-state
- Rust-first core engine: `ta/rust/crates/ta-engine`
- Python bindings package: `ta/rust/crates/ta-py` consumed by `laakhay-ta`
- Stable FFI crate: `ta/rust/crates/ta-ffi`
- Optional Node wrapper later: `ta/rust/crates/ta-node`
- Python layer keeps DSL/planner ergonomics but delegates heavy compute to Rust.

## Branch strategy
- Branch: `feat/rust-first-replatform`
- Fast merge cadence, smaller PRs, but accept breaking changes.

---

## Commit 01: Hard reset architecture docs and constraints
### Intent
Officially declare Rust-first replatform and remove compatibility guarantees.

### Touchpoints
- Edit: `ta/README.md`
- Create: `ta/docs/plans/rust-core-architecture-rfc.md`
- Edit: `ta/docs/plans/rust-core-modularization-commit-plan.md`

### Changes
- Declare beta-breaking policy.
- Define ownership split: Rust core vs Python orchestration.
- Freeze immediate technical choices:
  - PyO3 + maturin
  - Rust crates as canonical runtime implementation
  - no long-lived Python fallback requirement

### Done when
- Docs explicitly permit breaking changes for speed.

---

## Commit 02: Create Rust workspace and wire CI skeleton immediately
### Intent
Stand up Rust workspace before any incremental kernel porting.

### Touchpoints
- Create: `ta/rust/Cargo.toml`
- Create: `ta/rust/rust-toolchain.toml`
- Create: `ta/rust/crates/ta-engine/Cargo.toml`
- Create: `ta/rust/crates/ta-engine/src/lib.rs`
- Create: `ta/rust/crates/ta-ffi/Cargo.toml`
- Create: `ta/rust/crates/ta-ffi/src/lib.rs`
- Create: `ta/rust/crates/ta-py/Cargo.toml`
- Create: `ta/rust/crates/ta-py/src/lib.rs`
- Edit: `ta/.github/workflows/quality.yml`
- Create: `ta/.github/workflows/rust.yml`
- Edit: `ta/Makefile`

### Changes
- Add `cargo check/test/fmt/clippy` jobs now.
- Add make targets: `rust-check`, `rust-test`, `rust-lint`.

### Done when
- Rust CI runs on every PR.

---

## Commit 03: Switch Python packaging to maturin path (breaking)
### Intent
Avoid dual build systems; move directly to Rust-extension-centric packaging.

### Touchpoints
- Edit: `ta/pyproject.toml`
- Create: `ta/rust/crates/ta-py/pyproject.toml` (or maturin config equivalent)
- Edit: `ta/Makefile`
- Edit: `ta/README.md`
- Delete: legacy packaging-only config paths no longer used

### Changes
- Standardize local build/install on maturin workflow.
- Update contributor setup docs to Rust-aware flow.

### Done when
- `pip install -e .` (or documented dev command) builds Python package with Rust extension.

---

## Commit 04: Define canonical runtime contract in Rust first
### Intent
Force contract ownership into Rust to prevent Python contract drift.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/contracts.rs`
- Create: `ta/rust/crates/ta-ffi/include/ta_engine.h`
- Create: `ta/laakhay/ta/runtime/contracts.py`
- Create: `ta/tests/unit/runtime/test_contract_shapes.py`

### Changes
- Define canonical series/mask/error/result structures in Rust.
- Python contract objects mirror Rust contract types.

### Done when
- Contract tests validate Rust<->Python payload shape compatibility.

---

## Commit 05: Port rolling kernels + moving averages in one wave
### Intent
Move the biggest kernel family in one aggressive batch.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/rolling.rs`
- Create: `ta/rust/crates/ta-engine/src/moving_averages.rs`
- Edit: `ta/rust/crates/ta-engine/src/lib.rs`
- Edit: `ta/rust/crates/ta-py/src/lib.rs`
- Edit: `ta/laakhay/ta/primitives/rolling_ops.py`
- Edit: `ta/tests/parity/test_kernels.py`

### Changes
- Implement in Rust: `rolling_sum`, `rolling_mean`, `rolling_std`, `min/max`, `ema`, `rma`, `wma`.
- Route these primitives to Rust directly.

### Done when
- Existing tests for these kernels pass against Rust path.

---

## Commit 06: Delete migrated Python kernel internals immediately
### Intent
Prevent dual maintenance and force real dependency on Rust path.

### Touchpoints
- Edit: `ta/laakhay/ta/primitives/kernels/rolling.py`
- Edit: `ta/laakhay/ta/primitives/kernels/ema.py`
- Edit: `ta/laakhay/ta/primitives/rolling_ops.py`
- Delete: obsolete Python-only helper/kernel implementations
- Edit: `ta/tests/parity/test_batch_vs_incremental.py`

### Changes
- Keep only minimal glue code in Python.
- Remove fallback logic unless strictly required for test harness.

### Done when
- No duplicated kernel math remains in Python for migrated ops.

---

## Commit 07: Port momentum + volatility core together
### Intent
Aggressively migrate next heavy families as a single milestone.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/momentum.rs`
- Create: `ta/rust/crates/ta-engine/src/volatility.rs`
- Edit: `ta/rust/crates/ta-engine/src/lib.rs`
- Edit: `ta/rust/crates/ta-py/src/lib.rs`
- Edit: `ta/laakhay/ta/primitives/kernels/rsi.py`
- Edit: `ta/laakhay/ta/primitives/kernels/stochastic.py`
- Edit: `ta/laakhay/ta/primitives/kernels/atr.py`
- Edit: `ta/tests/integration/test_indicators_functional.py`

### Changes
- Move RSI, stochastic, ATR first-class to Rust.
- Any API adjustments needed for clean Rust contracts are allowed.

### Done when
- Momentum/volatility integration tests pass with Rust runtime.

---

## Commit 08: Port volume family and enforce Rust as default backend
### Intent
Finish high-usage indicator migration and stop treating Rust as optional.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/volume.rs`
- Edit: `ta/rust/crates/ta-engine/src/lib.rs`
- Edit: `ta/rust/crates/ta-py/src/lib.rs`
- Create: `ta/laakhay/ta/runtime/backend.py`
- Edit: `ta/laakhay/ta/__init__.py`
- Edit: `ta/laakhay/ta/indicators/volume/cmf.py`
- Edit: `ta/laakhay/ta/primitives/kernels/obv.py`
- Edit: `ta/laakhay/ta/primitives/kernels/klinger.py`
- Edit: `ta/tests/integration/test_explicit_source_indicators.py`

### Changes
- Rust becomes default and expected backend.
- Optional escape hatch can remain temporary (`LAAKHAY_TA_BACKEND=python`) for debugging only.

### Done when
- Main indicator families execute on Rust by default.

---

## Commit 09: Rework evaluator dispatch for batched Rust execution
### Intent
Capture full performance gain by reducing Python call overhead.

### Touchpoints
- Create: `ta/laakhay/ta/runtime/dispatch.py`
- Edit: `ta/laakhay/ta/expr/planner/evaluator.py`
- Edit: `ta/laakhay/ta/expr/execution/engine.py`
- Edit: `ta/laakhay/ta/primitives/adapters/registry_binding.py`
- Edit: `ta/tests/performance/test_evaluation_benchmarks.py`

### Changes
- Batch kernel invocations through Rust dispatch layer.
- Remove piecemeal Python invocation patterns where possible.

### Done when
- Benchmark delta shows clear runtime improvement over baseline.

---

## Commit 10: Introduce strict parity/perf gates and fail fast in CI
### Intent
Replace compatibility caution with hard quality gates.

### Touchpoints
- Create: `ta/tests/parity/golden/README.md`
- Create: `ta/tests/parity/golden/*.json`
- Create: `ta/tests/performance/benchmarks_baseline.json`
- Create: `ta/tests/parity/test_python_vs_rust_differential.py`
- Edit: `ta/.github/workflows/test.yml`
- Edit: `ta/.github/workflows/rust.yml`

### Changes
- CI fails if parity threshold breaks or perf regresses beyond agreed budget.
- Keep tolerances pragmatic, not over-conservative.

### Done when
- Every PR is blocked on parity+performance checks.

---

## Commit 11: Publish-ready Rust crates (engine + ffi)
### Intent
Make Rust reusable outside Python ecosystem now, not later.

### Touchpoints
- Edit: `ta/rust/crates/ta-engine/Cargo.toml`
- Edit: `ta/rust/crates/ta-ffi/Cargo.toml`
- Create: `ta/rust/README.md`
- Create: `ta/rust/crates/ta-engine/README.md`
- Create: `ta/rust/crates/ta-ffi/README.md`
- Edit: `ta/LICENSE`

### Changes
- Add crate metadata, features, docs, and publish checks.
- Ensure `ta-engine` is free from Python binding dependencies.

### Done when
- `cargo package` and local publish dry-run pass.

---

## Commit 12: Stabilize FFI ABI v1 early for cross-language consumers
### Intent
Lock a durable ABI now so Node/TS and other consumers can start quickly.

### Touchpoints
- Edit: `ta/rust/crates/ta-ffi/src/lib.rs`
- Edit: `ta/rust/crates/ta-ffi/include/ta_engine.h`
- Create: `ta/rust/crates/ta-ffi/tests/abi_smoke.rs`
- Create: `ta/docs/api/ffi-contract-v1.md`
- Create: `ta/tests/integration/test_ffi_smoke.py`

### Changes
- Freeze ABI symbols and versioning policy.
- Add ABI compatibility smoke checks.

### Done when
- ABI tests pass and docs define exact integration contract.

---

## Commit 13: Node/TypeScript scaffold immediately after ABI freeze
### Intent
Unblock future Node module without delaying current milestone.

### Touchpoints
- Create: `ta/rust/crates/ta-node/Cargo.toml`
- Create: `ta/rust/crates/ta-node/src/lib.rs`
- Create: `ta/docs/plans/ta-node-bindings-plan.md`
- Edit: `ta/rust/Cargo.toml`

### Changes
- Pick and document one direction now:
  - `napi-rs` direct binding to `ta-engine`, or
  - bridge via `ta-ffi`.

### Done when
- Node crate scaffold compiles and integration plan is explicit.

---

## Commit 14: Final cleanup pass and remove deprecated beta paths
### Intent
Remove transitional glue aggressively to keep codebase clean.

### Touchpoints
- Edit: `ta/laakhay/ta/runtime/backend.py`
- Edit: `ta/laakhay/ta/primitives/kernel.py`
- Delete: temporary fallback toggles and deprecated adapters
- Edit: `ta/README.md`

### Changes
- Remove temporary compatibility shims.
- Document new canonical runtime behavior.

### Done when
- Repository reflects one clear architecture, not migration scaffolding.

---

## What we are intentionally NOT doing
1. Long deprecation windows.
2. Maintaining full Python reference implementations for all kernels.
3. Preserving every old internal extension point if it slows migration.
4. Delaying ABI and Node planning until “later”.

## Fast execution order
1. Commit 01-04 in first sprint.
2. Commit 05-09 in second sprint (core runtime migration).
3. Commit 10-14 in third sprint (hardening + distribution).

## Success criteria
1. Core runtime-heavy indicators execute in Rust by default.
2. Python package builds and runs through Rust extension pipeline.
3. Rust crates are independently consumable.
4. FFI ABI v1 exists and is tested.
5. Codebase has minimal migration debt and no prolonged dual-path burden.
