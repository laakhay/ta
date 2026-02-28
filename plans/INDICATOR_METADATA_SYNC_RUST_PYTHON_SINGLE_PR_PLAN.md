# Laakhay-TA: Rust-First Indicator Compute + Python Ergonomics
## Single-PR, Commit-by-Commit Execution Plan

## 1. Objective
Deliver a single PR in `laakhay-ta` that makes Rust the compute runtime for all shipped indicators, while Python remains the ergonomics/orchestration layer (DSL, registry UX, API convenience).

Target outcome:
1. Every public indicator callable in Python executes Rust math.
2. Metadata contract is canonical in Rust and consumed by Python.
3. Python keeps DSL/planner/input ergonomics without owning indicator compute implementations.

## 2. Scope
In scope:
1. Define canonical Rust metadata model for indicators.
2. Expose complete Rust indicator catalog (`ta-engine`) for all indicators shipped by Python API.
3. Port all Python indicator compute paths to Rust kernels/functions.
4. Route Python indicator execution through `ta-py` Rust bindings.
5. Add synchronization and coverage gates that fail if any public indicator compute remains Python-only.
6. Add guardrails for output ordering, parameter validation schema, and warmup semantics.

Out of scope:
1. Drishya integration changes.
2. Hybrid/remote compute orchestration.
3. Replacing Python DSL/planner/orchestration layers in this PR.

## 3. Current-State Findings (Why this PR is needed)
1. Python currently has rich registry/schema/catalog constructs and many indicator implementations:
- `laakhay/ta/registry/schemas.py`
- `laakhay/ta/registry/registry.py`
- `laakhay/ta/catalog/catalog.py`
- `laakhay/ta/indicators/*`

2. Rust `ta-engine` exposes only a subset of indicator compute and minimal runtime contracts:
- `rust/crates/ta-engine/src/lib.rs`
- `rust/crates/ta-engine/src/contracts.rs`

3. Python bindings (`ta-py`) expose compute wrappers but no first-class metadata catalog endpoint:
- `rust/crates/ta-py/src/lib.rs`

Risks if unchanged:
- drift between runtimes,
- duplicate maintenance,
- Python compute bottlenecks for indicators not yet ported.

## 4. Design Principles
1. Rust is the single source of truth for indicator compute and shared metadata.
2. Python is the single source of truth only for ergonomics (DSL authoring, planner, adapter UX).
3. No hidden reflection assumptions; use explicit catalogs and deterministic ordering.
4. Sync and compute ownership are test-enforced, not policy-enforced.
5. Prefer additive compatibility shims during migration, then remove Python compute fallbacks before merge.

## 5. Canonical Metadata Contract (Target)
Rust-side canonical types (example names):
1. `IndicatorParamMeta`
- `name`, `kind`, `required`, `default`, `description`, constraints (`min`, `max`, `enum_values`)

2. `IndicatorOutputMeta`
- `name`, `kind` (`line`, `histogram`, `band`, `signal`, etc.), `description`, role metadata

3. `IndicatorSemanticsMeta`
- `required_fields`, `optional_fields`, `lookback_params`, `default_lookback`, `warmup_policy`, input slot defaults

4. `IndicatorMeta`
- `id`, `display_name`, `category`, `aliases`, `param_aliases`, `params`, `outputs`, `semantics`, `runtime_binding`

5. Public API
- `pub fn indicator_catalog() -> &'static [IndicatorMeta]`
- `pub fn find_indicator_meta(id: &str) -> Option<&'static IndicatorMeta>`

## 6. Single-PR Commit Plan

## Commit 1: Inventory and Migration Matrix (Python -> Rust)
Intent:
- Create explicit inventory of all public Python indicators and target Rust coverage.

File touchpoints:
1. `docs/indicator_porting_matrix.md` (new)
2. `laakhay/ta/indicators/__init__.py` (reference list verification if needed)
3. `tests/unit/catalog/test_catalog_coverage.py` (scaffold)

Acceptance criteria:
1. List of all publicly exposed indicators is frozen in-repo.
2. Each indicator has status: `ported`, `to_port`, `blocked` (with reason).
3. No ambiguity about what must be ported before merge.

## Commit 2: Introduce Rust Metadata Domain Models
Intent:
- Add canonical metadata structs/enums in `ta-engine` without behavior changes.

File touchpoints:
1. `rust/crates/ta-engine/src/contracts.rs` (or new `src/metadata.rs`)
2. `rust/crates/ta-engine/src/lib.rs` (module export)

Acceptance criteria:
1. Rust compiles.
2. Metadata types derive stable traits (`Debug`, `Clone`, `PartialEq`, optional `serde`).
3. No compute behavior change yet.

## Commit 3: Add Static Catalog Skeleton and Lookup APIs
Intent:
- Create explicit catalog container and stable lookup methods.

File touchpoints:
1. `rust/crates/ta-engine/src/metadata.rs` (new)
2. `rust/crates/ta-engine/src/lib.rs`

Acceptance criteria:
1. `indicator_catalog()` returns deterministic ordering.
2. `find_indicator_meta()` supports id and aliases.
3. Unit tests validate unique ids, unique aliases, deterministic ordering.

## Commit 4: Port Remaining Indicators to Rust Compute
Intent:
- Implement missing indicator math in Rust until it matches full Python public surface.

File touchpoints:
1. `rust/crates/ta-engine/src/momentum.rs`
2. `rust/crates/ta-engine/src/moving_averages.rs`
3. `rust/crates/ta-engine/src/rolling.rs`
4. `rust/crates/ta-engine/src/trend.rs`
5. `rust/crates/ta-engine/src/volatility.rs`
6. `rust/crates/ta-engine/src/volume.rs`
7. additional Rust modules as needed (`events`, `pattern`, etc.)

Acceptance criteria:
1. Every public Python indicator has a Rust compute implementation.
2. Multi-output ordering is explicit and consistent.
3. Parameter constraints and warmup behavior are represented.

## Commit 5: Populate Full Rust Catalog for All Ported Indicators
Intent:
- Add metadata entries for every Rust-backed indicator in the public surface.

File touchpoints:
1. `rust/crates/ta-engine/src/metadata.rs`
2. `rust/crates/ta-engine/tests/metadata_contract_tests.rs` (new)

Acceptance criteria:
1. Catalog includes all public indicators.
2. Output names/order match runtime outputs.
3. Semantics are complete (required fields, lookback metadata, warmup policy).

## Commit 6: Expose Rust Metadata and Compute Endpoints via ta-py
Intent:
- Make Python consume Rust catalog and complete Rust compute set.

File touchpoints:
1. `rust/crates/ta-py/src/lib.rs`

Changes:
1. Add `#[pyfunction] fn indicator_catalog() -> PyResult[list[dict]]` with fixed shape.
2. Add `#[pyfunction] fn indicator_meta(id: String) -> PyResult[dict]`.
3. Add any missing Python-callable wrappers for newly ported Rust indicators.
4. Register all endpoints in `#[pymodule]` exports.

Acceptance criteria:
1. Python can fetch full catalog from Rust binding.
2. All public indicator compute paths are callable via `ta_py`.
3. Binding payload shape is documented and stable.

## Commit 7: Add Python Runtime Bridge (Rust as Default/Required Compute)
Intent:
- Route Python indicator execution to Rust compute while keeping Python ergonomics.

File touchpoints:
1. `laakhay/ta/catalog/catalog.py`
2. `laakhay/ta/catalog/__init__.py`
3. `laakhay/ta/registry/registry.py`
4. optional `laakhay/ta/catalog/rust_catalog.py`

Changes:
1. Catalog API consumes Rust catalog as canonical metadata.
2. Registry/dispatch uses Rust compute backend for all public indicators.
3. Any temporary Python fallback is explicitly gated and marked migration-only.

Acceptance criteria:
1. Python APIs remain ergonomic and backward-compatible at interface level.
2. Indicator math executes in Rust for all public indicators.
3. Any non-Rust execution path is test-detected and disallowed before merge.

## Commit 8: Canonical Serialization Envelope and Contract Versioning
Intent:
- Standardize catalog serialization for parity tests and downstream consumers.

File touchpoints:
1. `laakhay/ta/catalog/serializer.py`
2. `laakhay/ta/catalog/utils.py`
3. Rust serializer helper in `ta-py`/`ta-engine` if needed
4. `docs/indicator_metadata_contract.md` (new)

Acceptance criteria:
1. Logical catalog serializes to canonical normalized JSON shape.
2. Deterministic key ordering and normalized defaults.
3. Contract versioning policy defined.

## Commit 9: Python Registry Alignment Pass (Ergonomics-Only Ownership)
Intent:
- Align Python registry/schema with Rust canonical envelope, retaining authoring ergonomics only.

File touchpoints:
1. `laakhay/ta/registry/schemas.py`
2. `laakhay/ta/registry/registry.py`
3. `laakhay/ta/registry/models.py`

Changes:
1. Shared fields map 1:1 to Rust canonical model.
2. Python-specific fields remain optional extension metadata.
3. Compute authority fields point to Rust runtime bindings.

Acceptance criteria:
1. No regression in registry tests.
2. No duplicate independent compute metadata authority in Python.

## Commit 10: Sync Tests (Rust Catalog vs Python Catalog)
Intent:
- Add automated drift prevention.

File touchpoints:
1. `tests/parity/test_indicator_metadata_sync.py` (new)
2. `tests/parity/utils.py` (reuse/extend)
3. optional fixtures under `tests/parity/golden/`

Test behavior:
1. Load Rust catalog via `ta_py.indicator_catalog()`.
2. Load Python catalog via package API.
3. Normalize and compare required shared fields:
- ids/aliases
- params (name/type/default/required/constraints)
- outputs (names/order/kind)
- semantics (required_fields/lookback/default_lookback/warmup)
- runtime binding identity

Acceptance criteria:
1. Drift fails CI.
2. No permanent allowlist for shared/public indicators.

## Commit 11: Compute Parity Tests (Python API -> Rust Math)
Intent:
- Prove Python public indicators are Rust-backed and numerically aligned.

File touchpoints:
1. `tests/parity/test_python_vs_rust_differential.py` (extend)
2. `tests/parity/test_indicator_compute_ownership.py` (new)
3. `tests/parity/golden/*` as needed

Checks:
1. Public Python indicator calls resolve to Rust backend.
2. Numerical parity against existing fixtures/tolerances.
3. Multi-output ordering/shape parity assertions.

Acceptance criteria:
1. Any Python-only compute path fails CI.
2. Indicator add/remove requires parity test updates.

## Commit 12: Coverage Tests for "All Indicators Exposed and Rust-Backed"
Intent:
- Enforce complete surface coverage and Rust ownership.

File touchpoints:
1. `tests/unit/catalog/test_catalog_coverage.py` (new/extend)
2. `rust/crates/ta-engine/tests/metadata_contract_tests.rs` (extend)
3. `docs/indicator_porting_matrix.md`

Checks:
1. Every public Python indicator appears in Rust catalog.
2. Every public Python indicator has Rust runtime binding.
3. Every Rust catalog entry has metadata + callable binding.

Acceptance criteria:
1. No silent missing metadata or missing Rust compute entries.
2. Porting matrix reaches 100% `ported` before merge.

## Commit 13: CI Wiring for Rust-Ownership Gates
Intent:
- Ensure metadata and compute-ownership tests run by default.

File touchpoints:
1. `Makefile`
2. `.github/workflows/*`
3. `pyproject.toml` / test config if needed

Acceptance criteria:
1. Metadata sync + compute ownership tests are required CI gates.
2. Rust and Python checks run deterministically.

## Commit 14: Final Hardening, Cleanup, and Documentation
Intent:
- Remove migration shims and document final contract.

File touchpoints:
1. cleanup across `catalog/*`, `registry/*`, indicator wrappers
2. `README.md`
3. `docs/indicator_metadata_contract.md`
4. `tests/parity/golden/indicator_catalog_v1.json` (new)

Acceptance criteria:
1. No dead code from pre-Rust compute paths.
2. No permanent Python indicator compute implementations for public surface.
3. All tests green (Python unit/integration/parity, Rust tests, binding smoke).

## 7. Test Matrix (Must Pass Before Merge)
Python:
1. `tests/unit/catalog/*`
2. `tests/unit/registry/*`
3. `tests/parity/test_indicator_metadata_sync.py` (new)
4. `tests/parity/test_indicator_compute_ownership.py` (new)
5. relevant integration smoke tests around API surface

Rust:
1. `rust/crates/ta-engine/tests/metadata_contract_tests.rs` (new)
2. existing `ta-engine` test suite
3. `ta-py` binding smoke for catalog + full indicator wrapper surface

Cross-runtime:
1. canonical metadata parity tests comparing normalized envelopes
2. compute parity tests from Python API calls to Rust outputs

## 8. Drift and Ownership Governance Rules
1. Adding/removing indicator requires:
- Rust compute implementation
- Rust catalog update
- Python ergonomic registration update
- sync/parity test update
- snapshot update

2. Multi-output changes require explicit ordering assertion updates.

3. Parameter default/constraint changes require snapshot and changelog note.

4. Public indicators cannot be merged as `python_only` compute.

## 9. PR Acceptance Criteria
Functional:
1. Rust exposes complete catalog for all public indicators.
2. Python exposes same canonical metadata and routes compute to Rust for all public indicators.
3. Metadata endpoints and compute ownership guarantees are documented.

Quality:
1. Drift tests fail on mismatch.
2. Compute ownership tests fail on any Python-only path.
3. Coverage tests prove no silent missing indicators.
4. Existing indicator behavior remains green within tolerance.

Compatibility:
1. Existing Python API signatures remain stable (or changes are explicitly versioned).
2. Python DSL/orchestration remains supported.
3. Breaking metadata shape changes require contract version bump.

## 10. Risks and Mitigations
1. Risk: Scope blow-up from full porting in one PR.
- Mitigation: inventory matrix, strict commit slicing, explicit blocked list with owner/date.

2. Risk: Numeric divergence during Rust ports.
- Mitigation: fixture-based differential tests, tolerances, and targeted golden updates.

3. Risk: Catalog shape churn breaks downstream consumers.
- Mitigation: versioned contract + changelog + snapshot review.

4. Risk: Python fallback paths silently persist.
- Mitigation: compute ownership CI gate + final cleanup commit removing fallback code.

## 11. Recommended Delivery Sequence
1. Commits 1-3: inventory + Rust metadata foundation.
2. Commits 4-7: full Rust compute port + binding + Python bridge.
3. Commits 8-12: canonical envelope + sync + compute ownership + coverage.
4. Commits 13-14: CI gates + cleanup/docs.

This sequence keeps Rust ownership enforceable at each stage and prevents permanent migration debt.

## 12. Post-PR Follow-ups (Optional)
1. Expose the same catalog and compute ownership guarantees via `ta-node` bindings.
2. Add machine-readable metadata export command for tooling/docs generation.
3. Extend metadata with compute complexity hints and incremental-compatibility flags.
