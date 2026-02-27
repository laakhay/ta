# Rust Incremental Backend PR Guide (Execution Runbook)

## 1. Goal and Operating Mode
Build and ship a Rust-native incremental runtime backend with canonical step semantics:

`(state, update) -> (new_state, output)`

This guide is optimized for:
- aggressive delivery speed
- architecture convergence to Rust runtime authority
- correctness via strict parity gates (not broad compatibility promises)

## 2. Scope

### In scope
1. Rust incremental runtime core in `ta-engine`
2. PyO3 bindings for incremental lifecycle
3. Python bridge backend delegating incremental execution to Rust
4. Snapshot/replay deterministic parity
5. CI gating for parity/replay correctness
6. Removal of legacy Python incremental internals once parity is green

### Out of scope
1. DSL parser/compiler rewrite in Rust
2. broad product/API redesign outside runtime execution
3. deep micro-optimizations beyond architecture-critical batching

## 3. PR Metadata

### 3.1 Recommended PR title
`feat(runtime): rust incremental backend with deterministic state-transition semantics`

### 3.2 PR description (drop-in)
This PR ports incremental runtime execution from Python to Rust and standardizes incremental processing around `(state, update) -> (new_state, output)` semantics.

#### Why
- Runtime-heavy batch paths are already Rust-backed.
- Incremental execution remained Python-centric and fragmented.
- This PR unifies runtime authority in Rust and reduces Python-side orchestration overhead for streaming/live workloads.

#### What
- New Rust incremental modules for contracts, state store, node adapters, kernel dispatch, and backend loop.
- PyO3 lifecycle bindings: initialize, step, snapshot, replay.
- Python bridge backend that routes incremental execution to Rust.
- Parity/replay CI gates; legacy Python incremental path removed only after parity locks.

#### Policy
This is a beta-speed migration PR. Compatibility is secondary to architecture convergence and deterministic correctness.

## 4. Current State Inventory (Python incremental path)
Current Python components to replace:
1. `laakhay/ta/expr/execution/backends/incremental.py`
2. `laakhay/ta/expr/execution/node_adapters.py`
3. `laakhay/ta/primitives/adapters/registry_binding.py`
4. `laakhay/ta/expr/execution/state/*`
5. tests coupling to old backend internals:
   - `tests/parity/test_batch_vs_incremental.py`
   - `tests/unit/expr/execution/test_drift_guard.py`
   - `tests/unit/expr/execution/test_node_adapters.py`

## 5. Target Architecture

### 5.1 Rust authority
- Rust owns incremental graph stepping, state transitions, and replay logic.
- Python orchestrates only bridge-level I/O and API adaptation.

### 5.2 Deterministic contract
For each node step:
- input: prior node state + resolved update payload
- output: new node state + optional output value

Global run invariants:
1. identical event stream -> identical output stream
2. snapshot + replay -> identical continuation output/state
3. deterministic node evaluation order per plan

### 5.3 Call granularity rule
Use coarse-grained calls:
- preferred: chunk/event-batch stepping with Rust-resident state handles
- avoid: chatty per-node Python<->Rust transitions

## 6. Detailed Commit Plan

---

## Commit 1: Lock design and invariants
### Intent
Freeze semantic contracts and migration constraints before code churn.

### Touchpoints
- Edit: `ta/docs/plans/rust-incremental-backend-pr-guide.md`
- Edit: `ta/docs/plans/rust-incremental-execution-migration-plan.md`
- Edit: `ta/docs/plans/rust-core-architecture-rfc.md`

### Deliverables
1. canonical incremental semantics section
2. determinism/replay guarantees
3. deletion criteria for Python legacy path

### Exit criteria
- semantic contract approved and unambiguous

---

## Commit 2: Rust incremental contract primitives
### Intent
Add durable Rust contract and state envelope types first.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/incremental/mod.rs`
- Create: `ta/rust/crates/ta-engine/src/incremental/contracts.rs`
- Create: `ta/rust/crates/ta-engine/src/incremental/state.rs`
- Edit: `ta/rust/crates/ta-engine/src/lib.rs`
- Create: `ta/rust/crates/ta-engine/tests/incremental_contracts_tests.rs`

### Deliverables
1. update payload structs/enums
2. node state envelope structs
3. snapshot envelope with `schema_version`
4. contract tests for (de)serialization compatibility assumptions

### Exit criteria
- contract tests pass; schema versioning wired

---

## Commit 3: Rust state store and lifecycle shell
### Intent
Establish node-state storage and lifecycle management in Rust.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/incremental/store.rs`
- Edit: `ta/rust/crates/ta-engine/src/incremental/state.rs`
- Create: `ta/rust/crates/ta-engine/tests/incremental_store_tests.rs`

### Deliverables
1. node-state map keyed by node ID
2. initialize/restore/snapshot primitives
3. deterministic state mutation API

### Exit criteria
- state store tests pass for initialize/snapshot/restore

---

## Commit 4: Port node adapters (non-call nodes)
### Intent
Port Python node adapter semantics for primitive IR node types.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/incremental/node_adapters.rs`
- Create: `ta/rust/crates/ta-engine/tests/incremental_node_adapters_tests.rs`

### Deliverables
Port behavior for:
1. source_ref
2. literal
3. unary
4. binary
5. filter
6. aggregate
7. timeshift

### Exit criteria
- Rust node adapter tests mirror Python adapter behavior for covered cases

---

## Commit 5: Rust kernel dispatch registry for incremental call nodes
### Intent
Move kernel resolution and coercion policy into Rust.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/incremental/kernel_registry.rs`
- Create: `ta/rust/crates/ta-engine/src/incremental/call_step.rs`
- Edit: `ta/rust/crates/ta-engine/src/incremental/mod.rs`
- Create: `ta/rust/crates/ta-engine/tests/incremental_call_step_tests.rs`

### Deliverables
1. runtime binding `kernel_id` -> Rust handler mapping
2. coercion rules for ATR/stochastic/etc.
3. deterministic call-step output behavior

### Exit criteria
- call-step tests pass for supported kernel IDs

---

## Commit 6: Rust incremental backend execution loop
### Intent
Implement full graph stepping backend in Rust.

### Touchpoints
- Create: `ta/rust/crates/ta-engine/src/incremental/backend.rs`
- Edit: `ta/rust/crates/ta-engine/src/incremental/mod.rs`
- Create: `ta/rust/crates/ta-engine/tests/incremental_backend_tests.rs`

### Deliverables
1. initialize(plan, history)
2. step(plan, tick)
3. snapshot(plan)
4. replay(plan, snapshot, events)

### Exit criteria
- backend tests pass for stepping and replay determinism

---

## Commit 7: Expose incremental lifecycle in PyO3 (`ta_py`)
### Intent
Provide stable Python binding surface for Rust incremental backend.

### Touchpoints
- Edit: `ta/rust/crates/ta-py/src/lib.rs`
- Edit: `ta/rust/crates/ta-py/Cargo.toml`
- Create: `ta/tests/parity/test_rust_incremental_bindings_smoke.py`

### Deliverables
Bindings:
1. `incremental_initialize(...)`
2. `incremental_step(...)`
3. `incremental_snapshot(...)`
4. `incremental_replay(...)`

### Exit criteria
- smoke tests can exercise entire lifecycle from Python

---

## Commit 8: Add Python bridge backend using Rust lifecycle
### Intent
Introduce runtime-usable bridge without deleting old backend yet.

### Touchpoints
- Create: `ta/laakhay/ta/expr/execution/backends/incremental_rust.py`
- Edit: `ta/laakhay/ta/expr/execution/backend.py`
- Edit: `ta/laakhay/ta/expr/execution/backends/__init__.py`

### Deliverables
1. resolver switch: `TA_INCREMENTAL_BACKEND=python|rust`
2. default = `rust` in this PR
3. fallback to python backend only for parity validation period

### Exit criteria
- end-to-end expressions can run via Rust incremental bridge

---

## Commit 9: Differential parity matrix (batch/python-incr/rust-incr)
### Intent
Prove correctness before deleting Python path.

### Touchpoints
- Create: `ta/tests/parity/test_incremental_python_vs_rust.py`
- Edit: `ta/tests/parity/test_batch_vs_incremental.py`
- Edit: `ta/tests/unit/expr/execution/test_drift_guard.py`
- Edit: `ta/tests/unit/expr/execution/test_node_adapters.py`

### Deliverables
Assertions:
1. batch == rust-incremental on covered expressions
2. python-incremental == rust-incremental
3. snapshot/replay parity exactness

### Exit criteria
- parity matrix passes in local + CI

---

## Commit 10: CI enforcement for incremental parity/replay
### Intent
Block regressions after cutover.

### Touchpoints
- Edit: `ta/.github/workflows/test.yml`
- Edit: `ta/.github/workflows/rust.yml`
- Edit: `ta/.github/workflows/quality.yml`

### Deliverables
1. required CI job for incremental parity suite
2. required CI replay determinism tests
3. optional benchmark smoke for boundary overhead

### Exit criteria
- merge blocked when incremental parity/replay breaks

---

## Commit 11: Remove Python incremental adapter stack (post-parity)
### Intent
Delete duplicated incremental node adapter infrastructure.

### Touchpoints
- Delete: `ta/laakhay/ta/expr/execution/node_adapters.py`
- Delete: `ta/laakhay/ta/primitives/adapters/registry_binding.py`
- Edit: `ta/laakhay/ta/primitives/adapters/__init__.py`
- Edit: imports referencing deleted modules

### Exit criteria
- no runtime references to deleted adapter modules

---

## Commit 12: Remove Python incremental backend (final cutover)
### Intent
Complete architecture convergence: Rust incremental only.

### Touchpoints
- Delete: `ta/laakhay/ta/expr/execution/backends/incremental.py`
- Edit: `ta/laakhay/ta/expr/execution/backends/__init__.py`
- Edit: `ta/laakhay/ta/expr/execution/backend.py`
- Edit: tests importing old backend directly

### Exit criteria
- only Rust incremental backend remains

---

## Commit 13: Documentation + operational runbook update
### Intent
Make new architecture operable and debuggable.

### Touchpoints
- Edit: `ta/README.md`
- Edit: `ta/docs/runtime/engine-and-evaluator.mdx`
- Edit: `ta/docs/testing/performance.mdx`
- Create: `ta/docs/testing/rust-incremental-parity.mdx`

### Deliverables
1. runtime topology docs
2. snapshot/replay debugging procedures
3. parity gate interpretation guide

### Exit criteria
- team can debug incremental runtime from docs alone

## 7. Validation Checklist (must pass before merge)
1. `make rust-check`
2. `make rust-test`
3. parity suite including incremental differential tests
4. replay determinism suite
5. Python integration smoke for common indicator expressions

## 8. Rollback Strategy
If parity gates fail late:
1. keep Rust modules merged behind `TA_INCREMENTAL_BACKEND=python`
2. retain Python incremental backend for one short stabilization PR
3. do not delete Python backend/adapters until parity returns green

## 9. Performance and boundary-overhead guardrails
1. avoid per-node per-tick Python-Rust calls
2. keep state handles resident in Rust across steps
3. batch replay events in chunks
4. track boundary overhead benchmark separately from kernel math benchmark

## 10. Commit Message Template
Use concise, atomic messages:
1. `docs: define rust incremental runtime contract`
2. `feat(rust): add incremental contracts and state store`
3. `feat(rust): port non-call incremental node adapters`
4. `feat(rust): add incremental kernel dispatch and call step`
5. `feat(rust): implement incremental backend loop and replay`
6. `feat(bindings): expose rust incremental lifecycle in ta_py`
7. `feat(runtime): add rust incremental python bridge`
8. `test(parity): add python-vs-rust incremental differential suite`
9. `ci: enforce incremental parity and replay checks`
10. `refactor: remove python incremental node adapter stack`
11. `refactor: remove legacy python incremental backend`
12. `docs: publish rust incremental runbook and troubleshooting`

## 11. Definition of Done
This plan is complete when:
1. incremental default path is Rust-backed
2. `(state, update) -> (new_state, output)` is explicit and tested
3. snapshot/replay parity is deterministic and CI-enforced
4. Python incremental legacy stack is removed (or intentionally deferred with explicit parity blocker issue)
