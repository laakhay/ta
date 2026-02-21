# TA DSL Architecture Refactor Plan (Critical Evaluation + Execution Roadmap)

Date: 2026-02-21
Scope: `ta/` library expression system, planner, evaluator, registry bootstrapping, and strategy-runtime correctness.

## Executive Verdict
Your assessment is directionally correct and technically strong.

The current architecture is functional, but it has real structural debt in four places:
1. Grammar boundary (Python-AST constraints + heuristics)
2. Multi-IR drift (DSL nodes vs algebra nodes vs API handle nodes)
3. Evaluation ownership ambiguity (node-level `evaluate` mixed with evaluator dispatch)
4. Source/registry determinism fragility (fallback key probing + import side-effects)

None of these are fatal today, but they will compound as features like richer events, structured outputs, streaming recompute, and UI expression builders scale.

## Critical Evaluation of Your Points

### 1) Replacing Python `ast` as DSL parser
Assessment: **Yes, best long-term move**.

What is true now:
- The parser is constrained by Python tokens/syntax that are not domain-native.
- Syntax wants to evolve toward trading-native addressing and richer operators.
- Error messages are necessarily Python-centric in edge cases.

Counterweight:
- Full parser rewrite is expensive and risky if done as a big-bang.

Recommendation:
- Keep current parser as compatibility mode short-term.
- Build grammar parser in parallel behind feature flag + dual-parse tests.
- Cut over only after parity and snapshot validation.

### 2) Canonical IR unification
Assessment: **Highest leverage structural fix**.

What is true now:
- There are multiple node systems with overlapping semantics (`expr/dsl/nodes.py`, `expr/algebra/models.py`, `api/handle.py`).
- Planning/evaluation/type validation paths can diverge subtly.

Recommendation:
- Define one canonical typed IR and route everything through it.
- Treat API handles and parser outputs as frontends that emit the same IR.

### 3) Add formal type system
Assessment: **Strongly recommended, medium implementation effort**.

What is true now:
- Many errors are discovered late at runtime.
- Multi-source and event indicators need stronger contracts than ad-hoc runtime checks.

Recommendation:
- Add a compact type lattice first (Series[number], Series[bool], Scalar[number], Scalar[bool], Structured output refs).
- Enforce indicator input/output typing in registry schema and compile-time validation.

### 4) Deterministic source resolution
Assessment: **Immediate correctness win**.

What is true now:
- Runtime key probing/fallbacks can produce non-obvious behavior as datasets grow.

Recommendation:
- Resolve source identities at compile/normalize phase.
- Evaluator should consume explicit resolved IDs only.

### 5) Evaluator ownership centralization
Assessment: **Correct and necessary**.

What is true now:
- Node classes have mixed evaluate responsibilities, including partial special-casing.

Recommendation:
- Make IR nodes pure data.
- Single evaluator dispatch executes semantics + caching + alignment policy.

### 6) Incremental hardening before major rewrite
Assessment: **Best risk-managed strategy**.

Yes: tightening heuristics, registry init, source keys, and tests now gives immediate safety and lowers migration risk.

## Proposed Target Architecture

Pipeline:
1. Parse (compat parser or grammar parser) -> raw AST
2. Normalize -> canonical IR (aliases, defaults, explicit source refs)
3. Typecheck -> typed IR + diagnostics with source spans
4. Plan -> data requirements + lookback/alignment graph
5. Evaluate -> deterministic executor over typed IR
6. Emit -> values + indicator emissions + debug metadata

Key principles:
- IR is single source of truth.
- Resolver is compile-time where possible; runtime is exact lookup only.
- Evaluator is pure execution layer, not parser/registry fallback layer.
- Every stage emits structured diagnostics.

## Refactor Plan (Phased)

## Phase 0: Guardrails + Baseline (1-2 weeks)
Goals:
- Freeze behavior, improve observability, reduce accidental regressions.

Tasks:
- Add golden snapshots for parse->IR, normalized IR, requirements manifest, and preview emissions.
- Add conformance test corpus for tricky expressions (multi-source, filters, structured indicator outputs, event indicators).
- Add stage-tagged diagnostic codes (`PARSE_*`, `TYPE_*`, `RESOLVE_*`, `EVAL_*`).

Deliverables:
- `tests/golden/expr/` fixtures + snapshot harness.
- Stability report: current heuristic/fallback paths and usage frequency.

## Phase 1: Determinism Hardening (1-2 weeks)
Goals:
- Remove ambiguous runtime behavior without changing external syntax.

Tasks:
- Make source resolution exact after normalization (no evaluator probing fallback chains).
- Move fallback behavior behind explicit compatibility flag.
- Make registry bootstrap explicit at process start (remove hidden import side-effect reliance).
- Standardize internal identifier formats for source refs and indicator outputs.

Deliverables:
- Resolver contract doc and implementation.
- Fallback compatibility mode with telemetry/deprecation warnings.

## Phase 2: Canonical IR Introduction (2-4 weeks)
Goals:
- Eliminate node-system drift.

Tasks:
- Define canonical IR schema (nodes, operator enums, source refs, indicator calls, projection/select nodes).
- Build adapters:
  - DSL parser output -> IR
  - API handle expressions -> IR
- Deprecate direct evaluator dependence on non-IR nodes.

Deliverables:
- `expr/ir/` module with schema + builders.
- Migration shims + parity tests.

## Phase 3: Type System + Validator (2-3 weeks)
Goals:
- Fail early and clearly.

Tasks:
- Implement minimal type lattice and inference pass.
- Annotate indicator registry entries with precise input/output signatures.
- Enforce boolean/numeric semantics for operators and filter conditions.
- Add structured-output projection typing (`bbands.upper`-style future support if adopted).

Deliverables:
- `expr/typecheck/` with diagnostics.
- Typechecked IR artifacts available to planner/evaluator.

## Phase 4: Evaluator Consolidation (2-3 weeks)
Goals:
- Single execution semantics.

Tasks:
- Remove ad-hoc node-level evaluate branching.
- Implement single-dispatch evaluator on canonical typed IR.
- Add deterministic cache keys (IR hash + dataset fingerprint + policy).
- Keep alignment policy centralized and explicit.

Deliverables:
- Unified evaluator module.
- Performance baseline and parity metrics.

## Phase 5: Grammar Parser Parallel Track (3-6 weeks, can overlap)
Goals:
- Future-proof syntax and diagnostics.

Tasks:
- Define formal DSL grammar (Lark recommended).
- Support current syntax subset first.
- Add better-native syntax extensions only after parity (optional).
- Run dual-parser mode in CI to ensure semantic equivalence against compatibility suite.

Deliverables:
- Grammar parser behind feature flag.
- Cutover readiness checklist + rollback flag.

## Phase 6: Structured Collections / Multi-leg Objects (future)
Goals:
- Support advanced objects/lists safely.

Tasks:
- Add aggregate selectors first (`any_*`, `nearest_*`, `count_*`) as safer bridge.
- If needed, add typed collection/object nodes in IR with strict projection semantics.

Deliverables:
- Design doc + prototype with bounded scope.

## Priority Refactors (Do First)
1. Source resolution determinism
2. Canonical IR definition and adapter path
3. Evaluator centralization
4. Minimal type system
5. Parser rewrite (parallel track)

## Concrete Changes Mapped to Current Code

Potential hotspots:
- Parser front-end: `ta/laakhay/ta/expr/dsl/parser.py`
- DSL nodes: `ta/laakhay/ta/expr/dsl/nodes.py`
- Algebra nodes/operators: `ta/laakhay/ta/expr/algebra/models.py`, `ta/laakhay/ta/expr/algebra/operators.py`
- API handle node overlap: `ta/laakhay/ta/api/handle.py`
- Evaluator dispatch + source lookup: `ta/laakhay/ta/expr/planner/evaluator.py`
- Registry initialization behavior: `ta/laakhay/ta/api/namespace.py`, `ta/laakhay/ta/registry/registry.py`

## Risk Register
- Regression risk in existing expressions: high unless dual-mode + snapshots.
- Performance regressions during IR/typecheck insertion: medium (mitigate with caching and benchmarks).
- Migration fatigue for downstream consumers: medium (mitigate with compatibility mode + explicit deprecations).

## Acceptance Criteria
- 100% parity on existing expression corpus in compatibility mode.
- Zero ambiguous source resolution in strict mode.
- All evaluator execution paths consume canonical typed IR.
- Type errors surfaced before evaluation with source spans.
- Deterministic requirement planning across runs.

## Recommendation Summary
- Your proposed direction is sound.
- Best practical strategy is **phased hardening + IR unification first**, grammar parser second.
- Avoid big-bang rewrite; use strict/compat modes and golden tests as safety rails.
