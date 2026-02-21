# Unified Semantics, Multi-Execution Engine Plan (Detailed)

## Objective
Design and implement a single semantic model for TA expressions with multiple execution modes, so the same expression has identical meaning regardless of runtime strategy.

Execution modes:
- `batch_vectorized`: evaluate on full historical arrays (current baseline)
- `incremental_stateful`: update outputs as new bars arrive using persistent node state

The core requirement is semantic equivalence, not just “similar output.”

## Scope

In scope:
- Expression runtime architecture in `ta`
- Indicator/kernel execution for currently active trend/momentum/volatility/volume/event indicators
- Runtime APIs (`evaluate`, `preview`, `stream`, replay/update behavior)
- Testing, parity gates, rollout control

Explicitly out of scope for this plan:
- `swing_*` and `fib_*` indicators (deferred intentionally)
- UI protocol redesign
- Cross-repo semantic changes (kendra/quantlab/data) before parity is proven inside `ta`

## Why This Matters
- Current runtime is primarily full recompute over `Series`, even in streaming wrappers.
- This is robust for correctness but expensive for live and long-running workloads.
- Incremental execution can provide major runtime gains, but only if semantics remain identical.
- The biggest failure mode in this migration is silent semantic drift; this plan is built to prevent that.

---

## Key Design Principles

1. One semantic pipeline
- Parse -> normalize -> typecheck -> plan must be mode-independent.
- Runtime mode cannot alter operator meaning, lookback interpretation, or mask semantics.

2. Runtime as pluggable backend
- Keep semantics above runtime.
- Runtime backend only decides execution mechanics, not meaning.

3. Batch runtime remains first-class
- Batch mode is not “legacy”; it is oracle + fallback.
- Incremental mode must prove parity against batch.

4. Explicit state model
- Stateful runtime must have typed, inspectable node state.
- Hidden mutable state is prohibited.

5. Replay correctness over raw speed
- Correction/backfill behavior must be deterministic.
- Performance optimizations are secondary to replay correctness.

---

## Target Architecture

### Semantic Layer (unchanged by mode)
- DSL parser (`expr/dsl`)
- IR nodes (`expr/ir`)
- normalize (`expr/normalize`)
- typecheck (`expr/typecheck`)
- planner (`expr/planner`) for dependency graph, alignment policy, requirements

### Runtime Layer (mode-specific)
- backend interface
- batch backend
- incremental backend

### State Layer (incremental only)
- node-level state schema
- state lifecycle manager
- invalidation/replay bookkeeping

### Kernel Layer
- pure kernels for vectorized compute
- state transition kernels for incremental step

---

## Semantic Parity Contract

Parity between modes means all of the following are equal for same input:
- timestamps
- values (exact for Decimal-based paths; tolerance rules only where required)
- availability mask
- trim/warmup
- multi-output ordering and keys
- behavior under append, correction, and replay

Any parity deviation is a runtime defect.

---

## Execution Model Contracts

### Batch mode contract
- Full graph evaluation over dataset snapshots.
- Stateless between calls (except optional memo cache per run context).

### Incremental mode contract
- `initialize(plan, history)` seeds node states and baseline outputs.
- `step(event)` consumes append events and updates dirty subgraph only.
- `replay(range)` recomputes affected region and refreshes downstream state.

## Migration Plan (Phase-by-Phase)

## Phase 0: Freeze Baseline Behavior

### Step 0.1: Build a behavior baseline matrix
Intent: capture current semantics before runtime refactor.
Purpose: prevent accidental reinterpretation of expression meaning.
Touchpoints:
- `ta/tests/unit/expr/*`
- `ta/tests/integration/*`
- Add golden fixtures for:
  - `sma`, `ema`, `macd`, `bbands`
  - `rsi`, `stochastic`
  - `atr`, `obv`, `vwap`
  - `cross*`, `in_channel/out/enter/exit`, `rising/falling/rising_pct/falling_pct`

### Step 0.2: Introduce a parity utility package
Intent: standardize parity assertions.
Purpose: avoid ad-hoc parity logic per test.
Touchpoints:
- New: `ta/tests/parity/utils.py`
- Checkers:
  - scalar series parity
  - tuple output parity
  - dict output parity
  - mask/timestamp parity
  - trim parity

---

## Phase 1: Runtime Backend Abstraction

### Step 1.1: Create backend protocol
Intent: isolate runtime implementations.
Purpose: switch execution modes without touching semantic layer.
Touchpoints:
- New: `ta/laakhay/ta/expr/runtime/backends/base.py`
- Required methods:
  - `evaluate(plan, dataset, options)`
  - `initialize(plan, dataset, options)`
  - `step(plan, update_event, options)`
  - `replay(plan, replay_spec, options)`
  - `snapshot(plan, options)`
  - `clear_cache()`

### Step 1.2: Wrap existing evaluator as batch backend
Intent: preserve current behavior behind new interface.
Purpose: refactor with zero semantic risk.
Touchpoints:
- New: `ta/laakhay/ta/expr/runtime/backends/batch.py`
- Reuse current logic from:
  - `ta/laakhay/ta/expr/planner/evaluator.py`
  - `ta/laakhay/ta/expr/runtime/evaluator.py` (if still needed)

### Step 1.3: Wire mode selector
Intent: add explicit execution mode control.
Purpose: controlled rollout and instant fallback.
Touchpoints:
- `ta/laakhay/ta/expr/runtime/engine.py`
- `ta/laakhay/ta/expr/runtime/stream.py`
- optional config/env:
  - `TA_EXECUTION_MODE=batch|incremental`

---

## Phase 2: Kernel Catalog and Standardization

### Step 2.1: Build kernel catalog
Intent: map every in-scope indicator to canonical kernel family.
Purpose: avoid duplicated logic in runtime backends.
Touchpoints:
- New: `ta/docs/kernel-catalog.md`
- Existing primitives:
  - `ta/laakhay/ta/primitives/_kernels.py`
  - `ta/laakhay/ta/primitives/__init__.py`

Canonical families:
- rolling reducers (sum/mean/std/min/max/arg*)
- recursive smoothers (ema/wilder variants)
- cumulative reducers (cumsum, obv, vwap internal components)
- boolean/event transitions (cross/channel/trend transitions)
- elementwise arithmetic/comparison kernels

### Step 2.2: Normalize indicator-to-kernel wiring
Intent: keep indicator functions declarative and pure.
Purpose: guarantee same semantics for all backends.
Touchpoints:
- `ta/laakhay/ta/indicators/trend/*`
- `ta/laakhay/ta/indicators/momentum/*`
- `ta/laakhay/ta/indicators/volatility/*`
- `ta/laakhay/ta/indicators/volume/*`
- `ta/laakhay/ta/indicators/events/*`

Acceptance:
- indicator implementations avoid nested evaluator recursion where possible
- each indicator has clear kernel path and warmup/mask definition

---

## Phase 3: Incremental State Model

### Step 3.1: Define node state schema
Intent: make incremental runtime deterministic and inspectable.
Purpose: support append and replay without hidden behavior.
Touchpoints:
- New: `ta/laakhay/ta/expr/runtime/state/models.py`

State fields per node:
- `node_id`
- `kernel_type`
- `last_processed_index` (or timestamp cursor)
- `warmup_status`
- `availability_status`
- `kernel_state_payload` (typed)
- `output_tail_cache` (optional bounded cache)
- `version_epoch`

### Step 3.2: Implement state store and lifecycle
Intent: centralize state mutations.
Purpose: avoid ad-hoc mutable state spread across backend code.
Touchpoints:
- New: `ta/laakhay/ta/expr/runtime/state/store.py`

Operations:
- initialize all node states
- get/update node state
- invalidate descendants
- create checkpoint and restore
- reset per symbol/timeframe/source partition

---

## Phase 4: Incremental Backend

### Step 4.1: Build dirty-propagation executor
Intent: execute only impacted nodes.
Purpose: reduce compute while preserving graph semantics.
Touchpoints:
- New: `ta/laakhay/ta/expr/runtime/backends/incremental.py`
- Uses planner graph dependencies and node order.

### Step 4.2: Implement append path
Intent: optimize for common live update (one new bar).
Purpose: O(changed_nodes) stepping.
Touchpoints:
- state transition kernels:
  - New: `ta/laakhay/ta/primitives/stateful/rolling.py`
  - New: `ta/laakhay/ta/primitives/stateful/ema.py`
  - New: `ta/laakhay/ta/primitives/stateful/cumulative.py`
  - New: `ta/laakhay/ta/primitives/stateful/events.py`

### Step 4.3: Implement correction/replay path
Intent: support data revisions and backfills.
Purpose: correctness when history changes.
Touchpoints:
- incremental backend `replay(...)`
- invalidation from replay start index
- downstream state rebuild from checkpoint or nearest safe anchor

---

## Phase 5: Testing and Benchmark Gates

### Step 6.1: Cross-mode parity suite
Intent: enforce one-semantics guarantee.
Purpose: CI-level safety net.
Touchpoints:
- New tests:
  - `ta/tests/parity/test_batch_vs_incremental.py`
  - `ta/tests/parity/test_replay_parity.py`
  - `ta/tests/parity/test_event_transition_parity.py`

### Step 6.2: Workload benchmarks
Intent: prevent performance regressions.
Purpose: ensure migration value is measurable.
Touchpoints:
- New benchmark harness:
  - append throughput
  - replay latency by window size
  - memory profile by indicator mix

Benchmark scenarios:
- single symbol/single timeframe
- multi-symbol common strategy set
- event-heavy expressions

---

## Phase 6: Integration Touchpoints

### Step 7.1: Runtime metadata surface
Intent: expose mode/debug state safely.
Purpose: operational transparency.
Touchpoints:
- `preview` and runtime result metadata:
  - mode used
  - replay stats
  - cache/state hit metrics

### Step 7.2: Kendra adoption path
Intent: adopt without breaking service behavior.
Purpose: controlled backend rollout.
Touchpoints:
- feature-flag mode selection in strategy preview/execution paths
- batch remains default until parity burn-in is complete

---

## Phase 7: Rollout and Risk Management

### Flags
- `TA_EXECUTION_MODE=batch|incremental`
- `TA_PARITY_SHADOW=true|false`
- `TA_PARITY_SAMPLE_RATE=<0..1>`

### Rollout sequence
1. Ship backend abstraction with batch-only behavior.
2. Enable incremental in shadow mode (compare to batch).
3. Promote incremental for selected environments.
4. Keep batch fallback permanently available.

### Major risks and mitigations
- Risk: semantic drift in event transitions
  - Mitigation: dedicated parity property tests and shadow diffs
- Risk: replay edge-case corruption
  - Mitigation: checkpoint/restore + deterministic replay tests
- Risk: hidden state bugs
  - Mitigation: explicit state schema + state introspection + invariant checks

---

## Concrete File Touchpoints

Create:
- `ta/laakhay/ta/expr/runtime/backends/base.py`
- `ta/laakhay/ta/expr/runtime/backends/batch.py`
- `ta/laakhay/ta/expr/runtime/backends/incremental.py`
- `ta/laakhay/ta/expr/runtime/state/models.py`
- `ta/laakhay/ta/expr/runtime/state/store.py`
- `ta/laakhay/ta/primitives/stateful/rolling.py`
- `ta/laakhay/ta/primitives/stateful/ema.py`
- `ta/laakhay/ta/primitives/stateful/cumulative.py`
- `ta/laakhay/ta/primitives/stateful/events.py`
- `ta/tests/parity/utils.py`
- `ta/tests/parity/test_batch_vs_incremental.py`
- `ta/tests/parity/test_replay_parity.py`
- `ta/tests/parity/test_event_transition_parity.py`
- `ta/docs/kernel-catalog.md`
- `ta/docs/execution-parity-contract.md`

Modify:
- `ta/laakhay/ta/expr/runtime/engine.py`
- `ta/laakhay/ta/expr/runtime/stream.py`
- `ta/laakhay/ta/expr/algebra/operators.py` (runtime routing only)
- `ta/laakhay/ta/expr/planner/evaluator.py` (batch backend extraction)
- `ta/laakhay/ta/expr/runtime/evaluator.py` (if retained)
- In-scope indicator files in:
  - `ta/laakhay/ta/indicators/trend/`
  - `ta/laakhay/ta/indicators/momentum/`
  - `ta/laakhay/ta/indicators/volatility/`
  - `ta/laakhay/ta/indicators/volume/`
  - `ta/laakhay/ta/indicators/events/`

Do not delete until rollout complete:
- existing batch evaluator path
- existing primitive kernels

---

## Definition of Done

1. Existing test suite remains green in batch mode.
2. New parity suite passes for all in-scope indicators/operators across modes.
3. Replay/correction parity passes under deterministic fixtures.
4. Benchmarks show incremental advantage for append workloads.
5. Batch fallback remains operational.
6. Runtime mode is configurable and observable.
7. Documentation reflects architecture, contracts, and operational guidance.

---

## Recommended Implementation Order (Execution-Friendly)

1. Backend interface + batch adapter.
2. Parity utility + baseline parity tests (batch vs batch adapter).
3. State schema/store.
4. Incremental kernels for rolling/ema/cumulative.
5. Incremental backend append path.
6. Event state kernels and parity tests.
7. Replay path.
8. Benchmark gates.
9. Shadow rollout and promotion.

This ordering minimizes risk and gives early confidence while delivering incremental value in measurable steps.
