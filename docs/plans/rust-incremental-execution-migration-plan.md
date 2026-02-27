# Rust Incremental Execution Migration Plan (No Premature Deletions)

## Objective
Port the existing incremental execution path to Rust in staged slices, while keeping current Python incremental behavior alive until Rust parity is proven.

## Current Python incremental stack to port
- `laakhay/ta/expr/execution/backends/incremental.py`
- `laakhay/ta/expr/execution/node_adapters.py`
- `laakhay/ta/primitives/adapters/registry_binding.py`
- incremental kernel classes under `laakhay/ta/primitives/kernels/*`
- parity guards:
  - `tests/parity/test_batch_vs_incremental.py`
  - `tests/unit/expr/execution/test_drift_guard.py`
  - `tests/unit/expr/execution/test_node_adapters.py`

## Migration rule
Do not remove Python incremental backend until Rust incremental backend reaches:
1. node-adapter parity
2. batch-vs-incremental parity
3. snapshot/replay parity

## Phase A: Rust incremental contracts
### Deliverables
- `rust/crates/ta-engine/src/incremental/contracts.rs`
- `rust/crates/ta-engine/src/incremental/state.rs`
- `rust/crates/ta-engine/src/incremental/mod.rs`

### Scope
- Define node-step input/output envelopes.
- Define state snapshot schema per node.
- Define deterministic timestamp/event ordering contract.

## Phase B: Rust node-step adapters
### Deliverables
- `rust/crates/ta-engine/src/incremental/node_adapters.rs`

### Scope
Port Python `node_adapters.py` behavior for:
- source_ref
- literal
- unary/binary ops
- filter
- aggregate
- timeshift

### Validation
- Add Rust unit tests mirroring `tests/unit/expr/execution/test_node_adapters.py` logic.

## Phase C: Rust incremental kernel registry
### Deliverables
- `rust/crates/ta-engine/src/incremental/kernel_registry.rs`

### Scope
- Map runtime binding `kernel_id` to Rust kernel implementations.
- Keep Python `registry_binding.py` as source behavior reference until cutover.

## Phase D: Rust incremental backend runtime
### Deliverables
- `rust/crates/ta-engine/src/incremental/backend.rs`
- PyO3 bindings in `rust/crates/ta-py/src/lib.rs`:
  - `incremental_initialize(...)`
  - `incremental_step(...)`
  - `incremental_snapshot(...)`
  - `incremental_replay(...)`

### Scope
- Port graph stepping loop from Python incremental backend.
- Support state-store semantics and replay behavior.

## Phase E: Python bridge layer
### Deliverables
- `laakhay/ta/expr/execution/backends/incremental_rust.py` (new bridge)
- runtime toggle in execution backend resolver:
  - `TA_INCREMENTAL_BACKEND=python|rust`

### Scope
- Keep default = `python` until parity locked.
- Allow side-by-side runs in tests.

## Phase F: Parity gates before cutover
### Deliverables
- Differential tests:
  - `tests/parity/test_incremental_python_vs_rust.py` (new)
- Extend existing:
  - `tests/parity/test_batch_vs_incremental.py`
  - `tests/unit/expr/execution/test_drift_guard.py`

### Gates
1. batch == python-incremental == rust-incremental on covered expressions
2. replay parity exact for deterministic fixtures
3. no regression in existing incremental tests

## Phase G: Cutover and cleanup
### Cutover steps
1. switch default incremental backend to Rust
2. run CI for two cycles with python fallback still available
3. remove Python incremental backend and node adapters

### Cleanup targets (only after Phase F passes)
- `laakhay/ta/expr/execution/node_adapters.py`
- `laakhay/ta/primitives/adapters/registry_binding.py`
- Python-only incremental kernels not used by batch paths

## Sequencing recommendation
1. A + B
2. C + D
3. E
4. F
5. G

## Acceptance criteria
- Rust incremental backend passes all existing incremental parity/drift/replay tests.
- Python incremental code can be deleted without loss of behavior.
