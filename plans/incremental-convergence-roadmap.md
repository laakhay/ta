# Incremental Convergence Roadmap

This is the living progress tracker for converging to one semantic model:

`(state, update) -> (next_state, output, availability)`

for all node execution, with `batch` and `incremental` as two runners over the same semantics.

## Current status snapshot

- Canonical evaluator path consolidated (`planner/evaluator.py` core, runtime wrapper legacy).
- Mode resolver centralized (`expr/execution/backend.py`) and wired in main entrypoints.
- Source/field schema unified (parser/typecheck/validate/manifest).
- [~] Parity harness expanded (`tests/parity/test_batch_vs_incremental.py` + utils) with nested, boolean, and time-shift cases.
- [~] Canonical step contract module introduced (`expr/execution/contracts.py`) with initial tests.
- [~] Incremental backend adapterization advanced; source/literal/binary/unary/call/timeshift/filter/aggregate logic delegated to `expr/execution/node_adapters.py`.
- [~] Single step runner entrypoint introduced (`expr/execution/runner.py`) and wired through `Expression.run`, `Engine`, and `Stream`.
- [~] Versioned state snapshots introduced under `expr/execution/state/*`.

## Phase A: Canonical Step Contract

Goal: define one execution contract every node must follow.

- [x] Add `expr/execution/contracts.py` with canonical step protocol:
  - node input shape
  - node state shape
  - output + availability semantics
- [x] Define warmup semantics explicitly (no implicit `None` ambiguity).
- [x] Define error/missing-data policy shared across modes.
- [x] Add unit tests for contract behaviors (`tests/unit/expr/execution/test_contracts.py`).

Exit gate:

- All node adapters can be validated against the same contract tests.

## Phase B: Shared Node Adapter Layer

Goal: remove backend-specific node behavior and route through one adapter registry.

- [x] Create `expr/execution/node_adapters.py` (or similar).
- [x] Move binary/unary/source/call/timeshift/filter/aggregate step logic into adapters.
- [x] Keep indicator-to-kernel binding inside primitives adapter layer only.
- [x] Remove residual hardcoded branching from incremental backend loop.

Exit gate:

- Incremental backend loop is graph-generic and delegates node behavior to adapters.

## Phase C: Single Runner, Two Modes

Goal: both execution modes use the same graph step runner.

- [x] Create `expr/execution/runner.py` as canonical graph runner.
- [~] Implement batch as historical replay over runner.
- [~] Implement incremental as streaming updates over runner.
- [x] Keep vectorized shortcuts optional and parity-guarded.

Exit gate:

- [x] `Expression.run`, `Engine`, and `Stream` route through one runner API.

## Phase D: State Model Unification

Goal: state lifecycle is explicit, typed, and replay-safe.

- [x] Introduce graph state model (`execution/state/*`) for node state snapshots.
- [~] Ensure snapshot/restore parity for batch replay and incremental continuation.
- [x] Add state schema/version metadata for forward compatibility.

Exit gate:

- [~] Replay tests and snapshot determinism tests pass.

## Phase E: Semantic Parity Hardening

Goal: prevent drift permanently via test gates.

- [~] Expand parity matrix:
  - nested indicators
  - multi-source expressions
  - boolean chains and comparison mixes
  - time shift / change / change_pct
  - warmup boundaries and availability transitions
- [ ] Add CI parity gate as mandatory.
- [~] Add targeted tolerance rules only where mathematically justified.

Exit gate:

- [~] Batch vs incremental parity suite passes for current expanded expression set; continue expanding goldens.

## Phase F: Compatibility Cleanup

Goal: remove temporary wrappers and stale modules once migration is complete.

- Migrate imports away from legacy runtime evaluator entrypoint.
- Remove `expr/runtime/evaluator.py` when zero references remain.
- Remove parser compatibility stubs only after callsites migrate.
- Keep changelog entries for migration-safe upgrades.

Exit gate:

- No stale wrappers remain except documented intentional API shims.

## Weekly progress checklist

Use this checklist each iteration:

- Identify one smallest next milestone (single merge-sized scope).
- Implement with focused file touch set.
- Run `make format && make lint-fix && make test`.
- Update this section checkboxes and status snapshot.
- Add/extend parity tests for the changed behavior.
- Commit atomically with conventional commit prefix and signed commit.

