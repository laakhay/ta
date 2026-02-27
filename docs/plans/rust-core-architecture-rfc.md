# RFC: Rust-First Runtime Replatform for `laakhay-ta`

## Status
- Draft (execution RFC)
- Applies to beta period only

## Decision summary
`laakhay-ta` will move to a Rust-first runtime architecture. Python remains the primary authoring and integration surface, but runtime-heavy compute paths are implemented in Rust and exposed through bindings.

This RFC intentionally allows breaking changes during beta to accelerate convergence to the target architecture.

## Why now
Current runtime hotspots are in kernel-heavy numeric paths. Maintaining high-performance implementations in Python increases long-term complexity and constrains future multi-language distribution.

A Rust-first core gives:
1. Better performance ceiling for rolling and indicator-heavy workloads.
2. Reusable core for Python, Rust-native, and future Node/TS consumers.
3. Clear runtime contracts instead of ad hoc per-language behavior.

## Scope
In scope:
1. Rust workspace and core engine crates.
2. Python bindings over Rust runtime.
3. FFI contract and ABI stabilization.
4. Removal of duplicated Python kernel internals once migrated.

Out of scope (for this migration wave):
1. Full DSL/parser rewrite.
2. Strategy semantics redesign.
3. OMS/execution responsibilities outside TA.

## Architecture boundaries
Rust owns:
1. Runtime-heavy indicator kernels.
2. Canonical numeric/runtime contracts.
3. FFI-safe compute entrypoints.

Python owns:
1. Public ergonomics layer.
2. DSL/planner and expression authoring UX.
3. Registry and high-level composition flow.

Rust crates:
1. `rust/crates/ta-engine`: pure Rust computational core.
2. `rust/crates/ta-ffi`: stable C ABI for non-Rust embedding.
3. `rust/crates/ta-py`: PyO3 bindings consumed by Python package.
4. `rust/crates/ta-node` (scaffold): future Node binding path.

## Beta compatibility policy
During beta:
1. Backward compatibility is not guaranteed.
2. Internal and public APIs may change if needed for cleaner Rust contracts.
3. Deprecated paths may be removed quickly after migration.

Post-beta:
1. API and ABI guarantees move to semver-based compatibility policy.

## Technical choices (frozen for this phase)
1. Python bindings: PyO3.
2. Build/package direction: maturin-centric flow.
3. Runtime source of truth: Rust implementations.
4. Fallback strategy: minimal/temporary Python fallback only where necessary.

## Migration strategy
1. Stand up Rust workspace + CI gates first.
2. Port highest-runtime kernels first (rolling + moving averages).
3. Route evaluator to batched Rust dispatch.
4. Enforce parity + performance gates in CI.
5. Publish Rust crates and stabilize FFI ABI early.
6. Remove duplicated Python runtime internals aggressively.

Execution plan reference:
- `docs/plans/rust-core-modularization-commit-plan.md`

## Quality gates
Every migration wave must satisfy:
1. Parity thresholds for covered indicators.
2. No unacceptable performance regression against benchmark baseline.
3. Deterministic behavior under test fixtures.

## Risks and mitigations
1. Risk: parity drift from numeric differences.
- Mitigation: explicit tolerance policy and golden fixtures.

2. Risk: packaging churn for contributors.
- Mitigation: single documented build path, no parallel packaging systems.

3. Risk: long-lived migration glue.
- Mitigation: explicit cleanup commits; delete temporary adapters quickly.

## Rollout checkpoints
1. Checkpoint A: Rust workspace + packaging path active.
2. Checkpoint B: rolling + moving averages migrated and Python internals pruned.
3. Checkpoint C: momentum/volatility/volume families migrated.
4. Checkpoint D: Rust default backend + evaluator dispatch optimized.
5. Checkpoint E: FFI ABI v1 stabilized + crates publish-ready.

## Acceptance criteria
Migration is considered successful when:
1. Core runtime-heavy indicator paths execute in Rust by default.
2. Python package builds and runs via Rust extension pipeline.
3. Rust crates are consumable independently.
4. ABI v1 contract exists and is covered by smoke tests.
5. Codebase has minimal dual-path debt.
