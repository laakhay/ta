# Laakhay-TA: Rust-Owned Dataset Execution Pipeline Plan
## Detailed Single-PR Blueprint (Rust Engine + Python API Surface)

## 0) PR Metadata
Branch name:
1. `feat/rust-dataset-execution-pipeline`

PR title:
1. `feat(engine): rust-owned dataset execution pipeline for python and rust apis`

PR objective:
1. Make dataset memory and execution path native (Rust) end-to-end.
2. Keep Python as ergonomics/planning/job-submission layer.
3. Ship fastest path to native execution with strict correctness/perf gates.

Success outcome (plain English):
1. Data is persisted in Rust buffers/handles.
2. Python API may change where needed for speed and clarity.
3. Python submits one execution job, Rust runs full graph.
4. No per-indicator Python<->Rust array ping-pong in hot path.

---

## 1) Current Gap vs Desired Model
Current model:
1. Python dataset/series often own memory.
2. Indicator wrappers call into Rust per indicator function.
3. Repeated conversion/marshaling around each call.

Desired model (numpy-like runtime semantics):
1. Python object is a facade over Rust-owned storage.
2. One job submission boundary for full graph/pipeline.
3. Rust owns stateful execution, dataset transforms, indicator kernels.
4. Python receives final outputs or output handles.

---

## 2) Guardrails (Non-Negotiable)
1. No fallback or shim paths in execution once Rust path lands.
2. No silent behavior drift: parity tests required at each major stage.
3. Prefer deletion over deprecation for obsolete Python compute paths.
4. Strict deterministic behavior for snapshot/replay and ordering.
5. Keep commits small and single-purpose.

---

## 3) Planned Commit Stack (Detailed)
Note:
1. Each commit message is proposed; adjust wording if needed.
2. Each commit includes intent, file touchpoints, and acceptance criteria.

## Commit 1
Message:
1. `feat(engine): add rust dataset handle registry and lifecycle`

Intent:
1. Introduce Rust-native dataset identity and lifecycle primitives.

File touchpoints:
1. `rust/crates/ta-engine/src/dataset.rs` (new)
2. `rust/crates/ta-engine/src/lib.rs`
3. `rust/crates/ta-engine/tests/dataset_handle_tests.rs` (new)

Core changes:
1. Add `DatasetId` generator and registry map.
2. Add create/get/drop APIs with typed errors.
3. Add stable error variants for unknown ids and invalid lifecycle calls.

Acceptance criteria:
1. `dataset_create()` returns unique ids.
2. `dataset_drop()` is deterministic and idempotence behavior is defined.
3. Unknown id access paths are tested.

---

## Commit 2
Message:
1. `feat(engine): implement columnar rust dataset storage and append validation`

Intent:
1. Store OHLCV/series as Rust-owned typed column buffers.

File touchpoints:
1. `rust/crates/ta-engine/src/dataset.rs`
2. `rust/crates/ta-engine/src/contracts.rs` (if shared dataset schemas are needed)
3. `rust/crates/ta-engine/tests/dataset_append_tests.rs` (new)

Core changes:
1. Add append APIs for OHLCV and named series.
2. Enforce timestamp/value length consistency.
3. Enforce symbol/timeframe/source invariants.

Acceptance criteria:
1. Append rejects shape mismatch with explicit error.
2. Append supports multi-symbol + multi-timeframe partitions.
3. Unit tests cover valid/invalid append paths.

---

## Commit 3
Message:
1. `feat(ta-py): expose rust dataset lifecycle and append endpoints`

Intent:
1. Publish handle and append APIs via Python bindings.

File touchpoints:
1. `rust/crates/ta-py/src/lib.rs`

Core changes:
1. Add pyfunctions:
   1. `dataset_create`
   2. `dataset_drop`
   3. `dataset_append_ohlcv`
   4. `dataset_append_series`
   5. `dataset_info`
2. Register all endpoints in module export.

Acceptance criteria:
1. Python smoke can create and append to Rust dataset.
2. Error mapping is stable (`ValueError`/`RuntimeError`/`KeyError` as appropriate).

---

## Commit 4
Message:
1. `feat(core): add rust-backed dataset facade in python core layer`

Intent:
1. Replace Python-owned dataset internals with Rust-owned handle semantics.

File touchpoints:
1. `laakhay/ta/core/dataset.py`
2. `laakhay/ta/runtime/contracts.py`
3. `laakhay/ta/runtime/backend.py`
4. `tests/unit/core/test_dataset.py` (extend)

Core changes:
1. Introduce internal `rust_dataset_id` ownership in dataset object.
2. Route append/ingest helper paths to ta-py dataset endpoints.
3. Remove Python-only in-memory dataset execution paths.

Acceptance criteria:
1. Dataset APIs operate through Rust handle only.
2. No Python data-path fallback remains for execution workloads.

---

## Commit 5
Message:
1. `feat(engine): add execute_plan entrypoint for rust-side graph execution`

Intent:
1. Introduce one-call graph submission to avoid per-node boundary traffic.

File touchpoints:
1. `rust/crates/ta-engine/src/incremental/backend.rs` (or `src/exec.rs` new module)
2. `rust/crates/ta-engine/src/contracts.rs`
3. `rust/crates/ta-py/src/lib.rs`
4. `rust/crates/ta-engine/tests/execute_plan_tests.rs` (new)

Core changes:
1. Add `execute_plan(dataset_id, plan_payload, options)` contract.
2. Parse/validate plan payload in Rust.
3. Return stable output envelope (ordered outputs, statuses, error messages).

Acceptance criteria:
1. Multi-node graph executes in one Rust call.
2. Output ordering is deterministic and tested.

---

## Commit 6
Message:
1. `refactor(runtime): route python rust backend through single plan submission`

Intent:
1. Make Python execution backend submit one Rust job instead of per-indicator calls.

File touchpoints:
1. `laakhay/ta/expr/execution/backends/incremental_rust.py`
2. `laakhay/ta/expr/execution/backends/batch.py`
3. `laakhay/ta/expr/execution/engine.py`
4. `laakhay/ta/expr/planner/manifest.py` (if payload normalization is needed)
5. `tests/unit/expr/execution/*` (extend)

Core changes:
1. Build normalized plan payload in Python.
2. Submit plan + dataset handle to Rust once.
3. Return new native-first response envelope; no compatibility adapter layer.

Acceptance criteria:
1. Expression tests pass using Rust execution backend exclusively.
2. Call-count instrumentation confirms reduced boundary crossings.

---

## Commit 7
Message:
1. `feat(engine): add rust dataset ops for align/resample/slice`

Intent:
1. Move heaviest dataset transforms to Rust core.

File touchpoints:
1. `rust/crates/ta-engine/src/dataset_ops.rs` (new)
2. `rust/crates/ta-engine/src/lib.rs`
3. `rust/crates/ta-py/src/lib.rs`
4. `laakhay/ta/primitives/elementwise_ops.py` (routing)
5. `tests/unit/primitives/test_elementwise_ops.py` (extend)

Core changes:
1. Rust ops for:
   1. align/join sync
   2. downsample
   3. upsample
   4. time-slice filter
2. Python wrappers become thin dispatchers.

Acceptance criteria:
1. Dataset-op parity against previous behavior is green.
2. No shape/timestamp regression in unit/parity tests.

---

## Commit 8
Message:
1. `refactor(engine): source indicator inputs directly from rust dataset storage`

Intent:
1. Remove per-indicator Python array extraction in runtime path.

File touchpoints:
1. `rust/crates/ta-engine/src/incremental/node_adapters.rs`
2. `rust/crates/ta-engine/src/incremental/kernel_registry.rs`
3. `rust/crates/ta-engine/src/dataset.rs`
4. `rust/crates/ta-engine/src/metadata.rs` (if binding metadata fields need updates)
5. `tests/parity/test_python_vs_rust_differential.py` (extend)

Core changes:
1. Node adapters fetch columns by dataset handle + field metadata.
2. Kernel execution reads Rust buffers directly.

Acceptance criteria:
1. No per-indicator marshaling path in runtime hot loop.
2. Parity suite remains green.

---

## Commit 9
Message:
1. `test(parity): add rust-dataset vs python-surface parity suite`

Intent:
1. Prevent semantic drift while moving ownership.

File touchpoints:
1. `tests/parity/test_dataset_rust_vs_python.py` (new)
2. `tests/parity/utils.py`
3. `tests/parity/test_indicator_metadata_sync.py` (adjust if needed)

Core checks:
1. Same timestamps/order/value semantics on representative graphs.
2. Multi-output ordering parity.
3. Snapshot/replay determinism parity.

Acceptance criteria:
1. New parity suite passes consistently in CI.

---

## Commit 10
Message:
1. `test(perf): add throughput and boundary-crossing benchmarks`

Intent:
1. Quantify speed and enforce regressions.

File touchpoints:
1. `tests/performance/test_pipeline_throughput.py` (new)
2. `tests/performance/test_boundary_crossings.py` (new)
3. `.github/workflows/test.yml` (if perf job enabled) or docs gate note

Core checks:
1. End-to-end pipeline throughput vs baseline.
2. Boundary crossing count per execution path.

Acceptance criteria:
1. Perf improvement documented and thresholded.

---

## Commit 11
Message:
1. `feat(runtime): make rust dataset execution default backend`

Intent:
1. Flip default runtime to Rust-owned data path.

File touchpoints:
1. `laakhay/ta/runtime/backend.py`
2. `laakhay/ta/core/dataset.py`
3. `README.md`
4. `docs/runtime/*` (as needed)

Core changes:
1. Default backend selects Rust dataset execution.
2. Remove opt-out path; Rust backend is mandatory for execution.

Acceptance criteria:
1. Default local run path uses Rust-owned dataset backend.
2. Legacy execution path is deleted from runtime.

---

## Commit 12
Message:
1. `chore(cleanup): remove transitional shims and fallback execution loops`

Intent:
1. Remove temporary migration paths once parity and perf are green.

File touchpoints:
1. `laakhay/ta/expr/execution/backends/*`
2. `laakhay/ta/primitives/*` (obsolete bridges only)
3. `docs/runtime/*`
4. `tests/*` updates tied to removed shims

Acceptance criteria:
1. No fallback per-indicator loop remains anywhere in execution path.
2. CI matrix fully green after cleanup.

---

## 4) Cross-Language API Contract (Must Be Stable)
Contract note:
1. Surface may change in this PR if it materially improves speed/engine clarity.
2. Stability target applies after this migration lands.

Dataset handle endpoints:
1. `dataset_create`
2. `dataset_drop`
3. `dataset_append_ohlcv`
4. `dataset_append_series`
5. `dataset_info`

Execution endpoint:
1. `execute_plan(dataset_id, plan_payload, options)`

Output contract requirements:
1. deterministic key ordering
2. explicit output ordering for multi-output nodes
3. clear status + error envelope fields

---

## 5) Required Validation Matrix Before Merge
Python:
1. `make ci`
2. parity tests:
   1. metadata sync
   2. compute ownership
   3. dataset parity (new)
3. runtime guardrails tests

Rust:
1. `make rust-fmt`
2. `make rust-lint`
3. `make rust-test`
4. `make build`

Cross-runtime:
1. expression parity suite
2. snapshot/replay determinism
3. boundary-crossing reduction validation
4. throughput benchmark validation

---

## 6) Rollout Risk Controls
1. Introduce dataset handle APIs before switching default backend.
2. Use versioned plan payload schema for execution endpoint.
3. Lock parity tests before deletion commits.
4. Remove obsolete paths as soon as Rust path is verified.
5. Keep commit granularity tight so regressions are isolated fast.

---

## 7) Out of Scope (This PR)
1. Rewriting Python DSL/planner entirely in Rust.
2. Distributed/remote execution orchestration.
3. Full node ecosystem migration (`ta-node`) beyond exposed execution surface.

---

## 8) Completion Definition
This PR is complete when all conditions are true:
1. Rust owns dataset memory for default execution path.
2. Python submits jobs; Rust executes graph in one call path.
3. Indicator + dataset op runtime no longer bounces arrays per node.
4. Python and Rust feature surfaces remain aligned for shipped functionality.
5. Legacy compatibility with pre-migration execution internals is removed.
6. All CI, parity, and perf gates are green.
