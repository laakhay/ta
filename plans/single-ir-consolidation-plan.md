# Single-IR Consolidation Plan for `ta/`

Date: 2026-02-21
Goal: move the expression system to a **single canonical IR** first, while preserving current functionality and minimizing drift risk. Parser replacement comes later.

## Scope and Non-Goals

## In scope
- Introduce one canonical expression IR used by compile, plan, evaluate, preview.
- Remove parallel/stale expression node paths that duplicate semantics.
- Keep current Python-AST parser as frontend adapter only.
- Keep all current DSL/user behavior compatible (compat mode), unless explicitly marked strict.

## Out of scope (this phase)
- New grammar parser implementation.
- Major syntax changes.
- Feature expansion beyond parity.

## Target Architecture (After Refactor)

```text
text expression
  -> parser adapter (python-ast for now)
  -> Parsed IR (canonical)
  -> normalize
  -> validate (minimal typecheck + semantic checks)
  -> plan
  -> execute
  -> preview/backtest outputs
```

Design rule: **Only canonical IR enters planner/evaluator/runtime.**
No runtime path should depend on old DSL-node or algebra-node classes.

## Current Duplication to Eliminate

Today, expression semantics are spread across:
- `ta/laakhay/ta/expr/dsl/nodes.py`
- `ta/laakhay/ta/expr/algebra/models.py`
- `ta/laakhay/ta/api/handle.py` (`IndicatorNode` overlap)
- evaluator fallbacks in `ta/laakhay/ta/expr/planner/evaluator.py`

This creates behavior drift risk and fragile execution ownership.

## Canonical IR Definition (single source of truth)

Canonical nodes (minimum set for parity):
- `LiteralNode`
- `SourceRefNode` (fully-resolved source/field identity, not ad-hoc string probing)
- `CallNode` (indicator/function call, named args normalized)
- `BinaryOpNode`
- `UnaryOpNode`
- `FilterNode`
- `AggregateNode`
- `TimeShiftNode`
- `MemberAccessNode` (for future structured outputs, keep gated)
- `IndexNode` (for future structured outputs, keep gated)

Every node includes:
- `span_start`, `span_end` (source diagnostics)
- stable serialization shape (for snapshot tests)

## File-by-File Refactor Plan

## A) Create (new files)

1. `ta/laakhay/ta/expr/ir/__init__.py`
- Purpose: canonical IR public exports.
- Effect: single import surface for all runtime/planner modules.

2. `ta/laakhay/ta/expr/ir/nodes.py`
- Purpose: dataclass definitions for canonical IR nodes + unions.
- Effect: removes ambiguity from multiple node systems.

3. `ta/laakhay/ta/expr/ir/serialize.py`
- Purpose: `ir_to_dict` / `ir_from_dict` for stable snapshots and API transport.
- Effect: deterministic contracts for tests and downstream systems.

4. `ta/laakhay/ta/expr/ir/types.py`
- Purpose: minimal type tags (`series_number`, `series_bool`, `scalar_number`, etc.).
- Effect: supports early validation and safer planner/evaluator behavior.

5. `ta/laakhay/ta/expr/normalize/__init__.py`
6. `ta/laakhay/ta/expr/normalize/normalize.py`
- Purpose: alias expansion, default args, source canonicalization, positional->named arg normalization.
- Effect: parser stays syntax-only; semantics become centralized.

7. `ta/laakhay/ta/expr/typecheck/__init__.py`
8. `ta/laakhay/ta/expr/typecheck/checker.py`
- Purpose: minimal compile-time type checks for operator and indicator-call validity.
- Effect: fewer runtime surprises and clearer diagnostics.

9. `ta/laakhay/ta/expr/parser/adapter.py`
- Purpose: parser interface (`ParserAdapter`) returning canonical IR.
- Effect: future grammar parser swap becomes trivial.

10. `ta/laakhay/ta/expr/parser/python_ast_adapter.py`
- Purpose: wrap existing python-ast parser and emit canonical IR.
- Effect: backward-compatible frontend while decoupling internals.

11. `ta/tests/unit/expr/ir/test_ir_roundtrip.py`
- Purpose: serialization roundtrip and stability tests.
- Effect: locks IR contract.

12. `ta/tests/unit/expr/normalize/test_normalize.py`
- Purpose: normalize behavior parity tests.
- Effect: catches semantic drift.

13. `ta/tests/unit/expr/typecheck/test_typecheck.py`
- Purpose: operator/input validation tests.
- Effect: compile-time safety net.

14. `ta/tests/golden/expr/*.json` (new fixtures)
- Purpose: canonical snapshots for parse->normalize->typed IR.
- Effect: migration safety and future parser parity checks.

## B) Edit (existing files)

1. `ta/laakhay/ta/expr/dsl/parser.py`
- Change: stop returning old DSL nodes directly for runtime use.
- New role: frontend translator into canonical IR via adapter.
- Effect: parser remains but is no longer semantic owner.

2. `ta/laakhay/ta/expr/planner/evaluator.py`
- Change: accept only canonical typed IR nodes.
- Remove: node-class-specific fallback branches tied to legacy systems.
- Effect: deterministic evaluator semantics.

3. `ta/laakhay/ta/expr/planner/planner.py` (and related planner modules)
- Change: consume canonical IR only.
- Effect: requirement planning no longer tied to legacy node classes.

4. `ta/laakhay/ta/expr/runtime/preview.py`
- Change: compile path must go through canonical IR pipeline.
- Effect: preview/backtest/analysis share exact same compile/runtime semantics.

5. `ta/laakhay/ta/api/handle.py`
- Change: `IndicatorHandle` should build canonical IR call nodes, not alternate internal node types.
- Effect: API and DSL converge on same execution model.

6. `ta/laakhay/ta/api/namespace.py`
- Change: ensure public API helpers produce canonical IR expressions.
- Effect: eliminate API-vs-DSL semantic drift.

7. `ta/laakhay/ta/expr/dsl/__init__.py`
- Change: expose compile helpers that return canonical IR artifacts.
- Effect: stable API boundary for callers.

8. `ta/docs/expression-language/*.mdx`
- Change: document canonical compile pipeline and strict/compat behavior.
- Effect: user clarity and lower misuse.

9. `ta/docs/runtime/*.mdx`, `ta/docs/planner/*.mdx`
- Change: update diagrams and contracts to canonical IR flow.
- Effect: docs match implementation.

## C) Delete (after parity is proven)

Delete only when all references are removed and parity tests pass.

1. `ta/laakhay/ta/expr/dsl/nodes.py`
- Reason: replaced by canonical IR nodes.
- Effect: removes one major duplicate AST model.

2. Legacy expression-node dependencies in `ta/laakhay/ta/expr/algebra/models.py` that overlap canonical IR
- Reason: avoid dual node universes.
- Effect: centralizes semantics.

3. Legacy `IndicatorNode` implementation path in `ta/laakhay/ta/api/handle.py` (class or compatibility branch)
- Reason: overlap/confusion with other node classes.
- Effect: one consistent expression representation.

4. Any evaluator fallback code for legacy node types in `ta/laakhay/ta/expr/planner/evaluator.py`
- Reason: hidden behavior divergence.
- Effect: deterministic execution.

## Migration Phases (Concrete)

## Phase 1: Introduce canonical IR in parallel (no deletions)
- Create all new `expr/ir`, `normalize`, `typecheck`, parser adapter modules.
- Add compile path: `parse -> normalize -> typecheck` producing canonical IR.
- Keep legacy path running for comparison in tests.

Exit criteria:
- Golden parity fixtures for key expressions pass in both paths.

## Phase 2: Switch planner/evaluator/runtime to canonical IR
- Planner/evaluator/preview consume only canonical IR.
- API handle/namespace emit canonical IR.
- Legacy node support remains only as temporary shims.

Exit criteria:
- Existing unit/integration tests pass without relying on old nodes.

## Phase 3: Remove stale files/branches
- Delete `expr/dsl/nodes.py` and legacy evaluator branches.
- Remove old node imports/re-exports.
- Finalize docs and compatibility notes.

Exit criteria:
- No import references to old node classes.
- Snapshot and runtime parity maintained.

## Compatibility Strategy

- Add `mode="compat" | "strict"` in compile API.
- `compat` preserves old shorthand behaviors where needed.
- `strict` enforces deterministic source refs and typed operator constraints.
- Track usage of compat fallbacks in diagnostics/telemetry and deprecate gradually.

## Public API Surface (Post-Refactor)

Keep stable, minimal surface:
- Canonical API names:
  - `compile_expression(text, mode="compat") -> CompiledExpression`
  - `validate_expression(compiled) -> ValidationReport`
  - `plan_expression(compiled, dataset_meta) -> ExecutionPlan`
  - `execute_expression(compiled, dataset, plan=None) -> EvalResult`
  - `preview_expression(compiled, dataset, options=...) -> PreviewResult`

Legacy compatibility (same behavior, wrappers calling canonical names):
- `analyze_expression(...)` -> calls `validate_expression(...)`
- `evaluate_expression(...)` -> calls `execute_expression(...)`

Deprecation policy:
- Keep legacy aliases for at least one minor cycle.
- Emit structured deprecation warning with migration hint in compat mode.

Internals (`expr/ir/*`, parser adapters, checker, normalize) should be private by convention.

## Risks and Mitigations

1. Regression from semantic shifts
- Mitigation: golden snapshots + dual-path tests in Phase 1.

2. Hidden callers using legacy node classes directly
- Mitigation: search + codemod + temporary deprecation wrappers.

3. Performance impact
- Mitigation: evaluator cache keys from canonical IR hash + dataset fingerprint.

4. Incremental merge complexity
- Mitigation: phase-gated PRs with explicit exit criteria.

## Acceptance Criteria

1. Single canonical IR is the only representation used in planner/evaluator/runtime.
2. Legacy node files are deleted or inert (no runtime references).
3. Existing expression features remain functional under compat mode.
4. Strict mode exists with deterministic source resolution and minimal type checks.
5. Docs reflect final architecture and API surface.

## Recommended PR Breakdown

1. PR-1: Add canonical IR + serializer + tests.
2. PR-2: Add normalize + typecheck + parser adapter.
3. PR-3: Route planner/evaluator/runtime through canonical IR.
4. PR-4: Migrate API handle/namespace to canonical IR.
5. PR-5: Add canonical API names (`validate_*`, `execute_*`) with legacy wrappers (`analyze_*`, `evaluate_*`).
6. PR-6: Delete stale node files/branches + finalize docs.
