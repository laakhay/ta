# TA Kernel + Runtime Semantics Refactor Plan

## Objective
Refactor `ta/` so expression semantics are explicit, execution is backend-isolated, indicator wiring is kernel-first, and repository organization is complete, readable, and low-indirection.

Primary outcomes:
1. One semantic pipeline (parse -> normalize -> typecheck -> plan).
2. Two execution modes (`batch`, `incremental`) using the same semantic plan.
3. One canonical runtime evaluator path (no duplicate evaluator stacks).
4. Kernel wiring model that is simple to read and easy to extend.
5. Remove stale/bloat safely, with explicit gates.

---

## Progress Update (Completed So Far)

### Completed summary
- Canonical evaluator core is now `expr/planner/evaluator.py`.
- `expr/runtime/evaluator.py` is now a legacy compatibility wrapper delegating to canonical evaluator behavior.
- Shared context/source resolution has been extracted to `expr/execution/context_builder.py` to remove duplicated evaluator logic.
- Primitives were modularized into focused modules (`select.py`, `rolling_ops.py`, `elementwise_ops.py`, `math_ops.py`) with kernel implementations centralized under `primitives/kernels/*`.
- Legacy primitive kernel split file `primitives/_kernels.py` has been removed after migration.
- Indicator import paths were migrated to modular primitive/kernel locations; expression-internal evaluation usage was removed in key indicators.

### Notes
- Completion marks below indicate implementation completion, not necessarily that all final phase exit tests (`make test`/parity) were run in this document context.

---

## Current State Audit (as of now)

### What is good
- IR exists (`expr/ir/*`) and compile pipeline exists (`expr/compile.py`).
- Runtime backends scaffold exists (`expr/runtime/backends/base.py`, `batch.py`, `incremental.py`).
- Kernel protocol exists in `primitives/kernel.py` with `initialize/step`.
- Incremental state store exists (`expr/runtime/state/*`).

### High-friction areas
1. Duplicate execution logic:
- `expr/planner/evaluator.py` and `expr/runtime/evaluator.py` both evaluate graphs with overlapping responsibilities.

2. Mode routing duplicated in multiple places:
- Mode selection (`TA_EXECUTION_MODE`) appears in `expr/runtime/engine.py`, `expr/algebra/operators.py`, and `expr/runtime/stream.py`.

3. Incremental backend has semantic coupling and ad-hoc behavior:
- `expr/runtime/backends/incremental.py` mixes graph stepping, indicator-specific branching, and hardcoded kernel lookup.

4. Kernel organization split across styles:
- `primitives/_kernels.py` (vector helper recipes) and `primitives/*.py` class kernels coexist.
- `primitives/__init__.py` is very large and mixed-concern.

5. Compatibility/fallback logic is spread:
- Backward-compat behavior across parser/planner/evaluator makes semantics difficult to reason about.

6. Bloat candidates:
- `tests/parity/debug_len.py` debug artifact.
- local cache folders (`__pycache__`) visible in tree.

---

## Target Architecture (Complete Repo Structure)

```text
ta/
  pyproject.toml
  Makefile
  README.md
  docs/
    architecture/
      expression-pipeline.md
      runtime-backends.md
      kernel-contract.md
      compatibility-policy.md
    reference/
      indicators.md
      expressions.md
      catalog.md
  plans/
    kernel-runtime-semantics-refactor-plan.md
    ...
  laakhay/
    ta/
      __init__.py
      exceptions.py

      api/
        __init__.py
        namespace.py            # ta.<group> ergonomic API
        handle.py               # user-facing expression/indicator handle wrappers
        execution.py            # thin API wrappers over expr.execute/preview

      catalog/
        __init__.py
        catalog.py              # listing/querying available indicators
        params.py               # param schema extraction
        serializer.py           # stable JSON export for UI/backend
        type_parser.py
        utils.py

      core/
        __init__.py
        types.py                # Price, Volume, scalar aliases
        timestamps.py
        bar.py
        ohlcv.py
        series.py
        context.py              # SeriesContext and context builders
        dataset.py
        coercers.py

      data/
        __init__.py
        csv.py
        dataset.py              # compatibility proxies to core.dataset

      registry/
        __init__.py
        models.py               # indicator handle metadata model
        schemas.py              # indicator schema + output metadata
        registry.py             # global and scoped registries

      indicators/
        __init__.py
        trend/
          __init__.py
          sma.py
          ema.py
          bbands.py
          macd.py
        momentum/
          __init__.py
          rsi.py
          stochastic.py
        volatility/
          __init__.py
          atr.py
        volume/
          __init__.py
          obv.py
          vwap.py
        events/
          __init__.py
          crossing.py
          channel.py
          trend.py
        pattern/
          __init__.py
          swing.py
          fib.py

      primitives/
        __init__.py             # thin re-export facade only
        kernel.py               # canonical kernel protocol
        math_ops.py             # generic numeric helpers (if needed)
        select.py               # source/field selectors + derived fields
        rolling_ops.py          # registered rolling primitives
        elementwise_ops.py
        kernels/
          __init__.py
          rolling.py            # RollingSum/Mean/Std kernel classes
          ema.py
          rsi.py
          atr.py
          cumulative.py         # obv/vwap internals if needed
          events.py             # event transition kernels if needed
        adapters/
          __init__.py
          registry_binding.py   # CallNode -> kernel binding + arg map
          warmup.py             # lookback/warmup helpers

      expr/
        __init__.py

        compile.py              # canonical compile entrypoint

        dsl/
          __init__.py
          parser.py             # text -> raw canonical IR nodes
          analyzer.py           # lightweight DSL-level helper analysis

        parser/
          __init__.py
          adapter.py            # parser backend interface (for future grammar swap)
          python_ast.py         # current python-ast parser backend implementation
          diagnostics.py        # parse error mapping and spans

        ir/
          __init__.py
          nodes.py              # canonical node classes
          types.py              # IR type tags and enums
          serialize.py          # stable IR serialization and snapshots
          visitors.py           # generic traversal utilities
          hashing.py            # deterministic IR hash utilities

        normalize/
          __init__.py
          normalize.py          # alias expansion, arg canonicalization
          rewrites.py           # explicit rewrite passes

        typecheck/
          __init__.py
          checker.py
          rules.py
          diagnostics.py

        semantics/
          __init__.py
          planner.py            # builds execution graph, requirements, alignment
          contracts.py          # trim/lookback/emission contracts
          requirements.py       # requirement extraction helpers
          analyzer.py           # inspect/analyze API core

        planner/
          __init__.py
          types.py              # PlanResult, graph node types
          builder.py            # graph construction helpers
          manifest.py           # requirement manifest construction
          planner.py            # legacy wrapper -> semantics.planner
          evaluator.py          # canonical graph evaluator core

        execution/
          __init__.py
          backend.py            # backend protocol + mode resolver
          runner.py             # single entry evaluate_plan
          batch.py              # batch backend implementation
          incremental.py        # incremental backend implementation
          stream.py             # stream orchestration on top of runner
          state/
            __init__.py
            models.py
            store.py

        runtime/
          __init__.py
          preview.py            # preview API wrapper around compile+execution
          validate.py
          analyze.py
          capability_validator.py
          emission.py
          engine.py             # compatibility wrapper over execution.runner
          evaluator.py          # temporary wrapper to planner/evaluator during migration

        algebra/
          __init__.py
          operators.py          # Expression wrapper and operator overloading only
          alignment.py
          scalar_helpers.py
          models.py             # legacy compatibility (planned deprecation)

  tests/
    conftest.py
    unit/
      core/
      registry/
      catalog/
      indicators/
      primitives/
      expr/
        dsl/
        parser/
        ir/
        normalize/
        typecheck/
        semantics/
        planner/
        execution/
        runtime/
        algebra/
    integration/
    e2e/
    parity/
    performance/
    golden/
      datasets/
      expectations/
      tools/
```

### Architecture principles for this structure
- `expr/ir/*` is canonical for expression representation.
- `expr/semantics/*` owns meaning; `expr/execution/*` owns runtime mechanics.
- `expr/runtime/*` is compatibility-oriented API surface, not core execution logic.
- `indicators/*` remain declarative and execution-mode-agnostic.
- `primitives/kernels/*` is the single home for kernel state transition code.

---

## Stage Responsibilities (Precise)

1. Parse (`expr/dsl`, `expr/parser`)
- Convert expression text into canonical raw IR nodes.
- Attach source spans and diagnostics.

2. Normalize (`expr/normalize`)
- Expand aliases, canonicalize args/kwargs, resolve shorthand forms.

3. Typecheck (`expr/typecheck`)
- Validate node/operator/indicator input-output compatibility.

4. Plan (`expr/semantics/planner`)
- Build graph order, requirements, lookback/trim, alignment policy.

5. Execute (`expr/execution`)
- Evaluate plan with selected backend.
- No parsing/normalization/typecheck in this stage.

6. Runtime APIs (`expr/runtime`)
- user-facing wrappers: preview, validate, analyze.
- may keep legacy signatures, but delegate internally.

---

## Step-by-Step Execution Plan

## Phase 0: Baseline Freeze and Safety Nets

### Step 0.1: Add architecture guard tests
Create:
- `tests/unit/expr/execution/test_backend_selection.py`
- `tests/unit/expr/execution/test_single_runtime_entrypoint.py`

Validate:
- single resolver behavior
- mode selection not duplicated outside central resolver

### Step 0.2: Snapshot behavior contracts
Create/extend:
- `tests/parity/test_batch_vs_incremental.py`
- planner/preview contract tests for trim, requirements, emissions

Exit gate:
- full `make test` green.

---

## Phase 1: Centralize Runtime Entry and Mode Resolution

### Step 1.1: Create centralized backend resolver
Create:
- `laakhay/ta/expr/execution/backend.py`

### Step 1.2: Create single runner entrypoint
Create:
- `laakhay/ta/expr/execution/runner.py`

### Step 1.3: Remove duplicate environment branching
Edit:
- `expr/runtime/engine.py`
- `expr/algebra/operators.py`
- `expr/runtime/stream.py`

Exit gate:
- only one module reads `TA_EXECUTION_MODE`.

---

## Phase 2: Consolidate Evaluator Paths

### Step 2.1: Canonical evaluator core
- [x] Use `expr/planner/evaluator.py` as canonical core.

### Step 2.2: Runtime evaluator becomes compatibility wrapper
Edit:
- [x] `expr/runtime/evaluator.py` delegates to canonical evaluator.
- [x] `expr/runtime/__init__.py` marks this legacy.

### Step 2.3: Move shared context/source resolution helpers
Create:
- [x] `expr/execution/context_builder.py` (or similar)

Exit gate:
- [x] no duplicated context/source resolution logic across evaluators.

---

## Phase 3: Kernel Wiring Cleanup

### Step 3.1: Introduce registry-to-kernel adapter
Create:
- `primitives/adapters/registry_binding.py`

### Step 3.2: Remove hardcoded indicator switch from incremental backend
Edit:
- `expr/execution/incremental.py` (or current backend file)

Replace with:
- adapter-driven kernel dispatch

### Step 3.3: Move indicator-specific edge behavior into adapters/kernels
Remove backend-level indicator hacks.

Exit gate:
- incremental backend loop is generic and node-driven.

---

## Phase 4: Primitives Decomposition

### Step 4.1: Split monolithic `primitives/__init__.py`
Create/Move:
- [x] `primitives/select.py`
- [x] `primitives/rolling_ops.py`
- [x] `primitives/elementwise_ops.py`
- [x] `primitives/__init__.py` reduced to thin re-export facade.

### Step 4.2: Consolidate kernels under `primitives/kernels/*`
- [x] Migrate class kernels here and keep facade exports stable.

### Step 4.3: Review `_kernels.py`
- [x] Reviewed and migrated.
- [x] Deleted `primitives/_kernels.py` after migration.

Exit gate:
- [x] contributors can locate primitive math and kernels quickly.

---

## Phase 5: Semantics Package Elevation

### Step 5.1: Create `expr/semantics/*` wrappers then migrate internal imports
Create:
- `semantics/planner.py`
- `semantics/contracts.py`
- `semantics/analyzer.py`

### Step 5.2: Keep legacy API signatures but route to new internals
- no external API break
- internal naming/organization clarity improved

Exit gate:
- internal imports favor `semantics` + `execution` namespaces.

---

## Phase 6: Stale/Bloat Cleanup

Immediate safe cleanup:
1. Delete `tests/parity/debug_len.py`.
2. Ensure `__pycache__/` and `*.pyc` are ignored and not tracked.

Conditional cleanup after migration gates:
1. Delete `expr/runtime/evaluator.py` (after all imports migrated).
2. Delete `expr/parser/adapter.py` only if parser abstraction is relocated and unused.
3. Delete `primitives/_kernels.py` only after full migration to modular helpers/kernels.

Safety gates before each delete:
- import grep shows no references
- `make test` passes
- parity suite passes

---

## Verification Matrix Per Phase

For each phase:
1. `make test`
2. parity tests for selected expressions (`batch` vs `incremental`)
3. targeted suites:
- `tests/unit/expr/*`
- `tests/integration/test_explicit_source_indicators.py`
- `tests/integration/test_multi_source_expressions.py`
- `tests/unit/indicators/*`

Additional checks:
- compile sanity for touched modules (`python -m compileall -q ...`)
- ensure no duplicate mode branching reintroduced

---

## File-Level Action Checklist

## Create
- `laakhay/ta/expr/execution/backend.py`
- `laakhay/ta/expr/execution/runner.py`
- [x] `laakhay/ta/expr/execution/context_builder.py`
- `laakhay/ta/expr/semantics/analyzer.py`
- `laakhay/ta/expr/semantics/planner.py`
- `laakhay/ta/expr/semantics/contracts.py`
- `laakhay/ta/primitives/adapters/registry_binding.py`
- [x] `laakhay/ta/primitives/select.py`
- [x] `laakhay/ta/primitives/rolling_ops.py`
- [x] `laakhay/ta/primitives/elementwise_ops.py`
- `tests/unit/expr/execution/test_backend_selection.py`
- `tests/unit/expr/execution/test_single_runtime_entrypoint.py`

## Edit
- `laakhay/ta/expr/runtime/engine.py`
- `laakhay/ta/expr/algebra/operators.py`
- `laakhay/ta/expr/runtime/stream.py`
- `laakhay/ta/expr/runtime/backends/incremental.py` (or moved execution equivalent)
- `laakhay/ta/expr/runtime/backends/batch.py` (or moved execution equivalent)
- [x] `laakhay/ta/expr/runtime/__init__.py`
- [x] `laakhay/ta/expr/planner/evaluator.py`
- [x] `laakhay/ta/primitives/__init__.py`
- `laakhay/ta/expr/compile.py` (if routing to semantics namespace)

## Delete (staged)
- `tests/parity/debug_len.py` (immediate)
- `laakhay/ta/expr/runtime/evaluator.py` (after migration)
- [x] `laakhay/ta/primitives/_kernels.py` (superseded and removed)
- any stale alias modules replaced by thin wrappers and then removed

---

## Risks and Mitigations

1. Backward compatibility regressions
- Mitigation: keep wrapper layer until imports and tests are migrated.

2. Incremental parity drift
- Mitigation: strict parity assertions on timestamps, availability, and values.

3. Over-abstraction
- Mitigation: enforce one runner + one resolver; avoid manager-of-manager patterns.

---

## Completion Criteria

Done when:
1. Semantic pipeline is single and mode-independent.
2. Runtime entrypoint is singular and explicit.
3. Mode selection exists in one place.
4. Incremental backend has no hardcoded indicator name switch logic.
5. Stale duplicate modules are removed or explicitly temporary wrappers.
6. Repo structure visually and logically reflects semantics vs execution vs kernels.

