# Rust Catalog + Runtime Parity Plan

## Branch
`feat/rust-catalog-runtime-parity`

## PR Title
`feat(core): make rust catalog authoritative and align python/node runtime contracts`

## Goal
Move core control-plane ownership (indicator catalog/metadata/capability validation) from Python to Rust so Python and Node become thin ergonomics layers over a shared Rust authority.

## Non-Goals (this PR)
- Full Rust DSL parser replacement.
- Full removal of Python registry decorators in one shot.
- Breaking external API names.

## Success Criteria
- Rust exposes authoritative catalog/spec metadata required by Python and Node.
- Python consumes Rust metadata for planner/catalog paths (no duplicate metadata authority).
- Graph capability checks are derived from Rust metadata.
- CI green: `make lint`, `make test-py`, `make test-rs`.

---

## Commit Plan

### Commit 1: Introduce Rust Catalog Contract v1 (authoritative shape)
**Intent**
- Define a stable Rust-side catalog contract that can power both Python and Node.

**Touchpoints**
- `crates/ta-engine/src/core/metadata.rs`
- `crates/ta-engine/src/core/contracts.rs`
- `crates/ta-engine/tests/metadata_contract_tests.rs`
- `crates/ta-engine/README.md`

**Changes**
- Add/normalize fields required by planner consumers:
  - id, aliases, params, default values, required fields, lookback hints, outputs.
- Add deterministic serialization ordering tests.

---

### Commit 2: Expose Catalog Contract Through FFI + ta-py
**Intent**
- Make Rust catalog queryable from Python and Node bindings through one path.

**Touchpoints**
- `crates/ta-ffi/src/lib.rs`
- `crates/ta-py/src/api/dataset.rs`
- `crates/ta-py/src/lib.rs`
- `crates/ta-py/README.md`

**Changes**
- Add `catalog_contract()` and `catalog_indicator(id)` style bindings.
- Ensure JSON-safe payloads and deterministic key ordering.

---

### Commit 3: Wire Python Catalog Layer to Rust Contract
**Intent**
- Make Python catalog builder/descriptor read from Rust contract, not Python-defined source-of-truth metadata.

**Touchpoints**
- `python/src/laakhay/ta/catalog/rust_catalog.py`
- `python/src/laakhay/ta/catalog/catalog.py`
- `python/src/laakhay/ta/catalog/serializer.py`
- `python/src/laakhay/ta/catalog/__init__.py`
- `python/tests/unit/catalog/test_catalog.py`
- `python/tests/parity/test_indicator_metadata_sync.py`

**Changes**
- Use Rust payload as primary input.
- Keep Python formatting/transformation only.
- Remove duplicate metadata assumptions in tests.

---

### Commit 4: Move Planner Capability Validation to Rust-Backed Metadata
**Intent**
- Ensure planner compatibility decisions rely on Rust authority.

**Touchpoints**
- `python/src/laakhay/ta/expr/runtime/capability_validator.py`
- `python/src/laakhay/ta/expr/planner/manifest.py`
- `python/tests/unit/expr/runtime/test_validate.py`

**Changes**
- Derive available indicators/operators/requirements from Rust catalog contract.
- Remove stale Python metadata branches.

---

### Commit 5: Minimize Python Registry Metadata Authority
**Intent**
- Turn Python registry metadata into compatibility shims (or remove where safe) so Rust remains single source of truth.

**Touchpoints**
- `python/src/laakhay/ta/registry/registry.py`
- `python/src/laakhay/ta/registry/schemas.py`
- `python/src/laakhay/ta/registry/__init__.py`
- `python/tests/unit/registry/test_registry.py`
- `python/tests/unit/registry/test_metadata.py`

**Changes**
- Remove or sharply reduce `_METADATA_HINTS` authority.
- Keep only runtime call signatures needed for ergonomics.

---

### Commit 6: Node Prep – Shared Catalog Consumption Path
**Intent**
- Ensure Node crate can consume exactly the same Rust catalog payload.

**Touchpoints**
- `crates/ta-node/src/lib.rs`
- `crates/ta-node/README.md`
- `docs/plans/ta-node-bindings-plan.md`

**Changes**
- Add catalog read endpoints in node bindings aligned to ta-py contract.
- Add smoke tests for shape parity.

---

### Commit 7: Dead-Code Cleanup + Docs Alignment
**Intent**
- Remove stale docs/tests referring to Python authority or old parity strategy.

**Touchpoints**
- `README.md`
- `VISION.md`
- `CONTRIBUTING.md`
- `python/README.md`
- `docs/api/registry-and-catalog.mdx`

**Changes**
- Document Rust-first metadata ownership.
- Update contributor guidance for adding indicators (Rust metadata first).

---

### Commit 8: Final Quality Gate
**Intent**
- Verify all checks and contracts before merge.

**Touchpoints**
- `.github/workflows/test.yml`
- `.github/workflows/rust.yml`

**Checks**
- `make lint`
- `make test-py`
- `make test-rs`
- targeted parity checks:
  - `python/tests/parity/test_indicator_metadata_sync.py`
  - `python/tests/parity/test_indicator_compute_ownership.py`

---

## Implementation Order Rationale
1. Lock contract in Rust first.
2. Expose via bindings.
3. Switch Python consumers.
4. Remove duplicate authority.
5. Prepare Node parity.

This avoids breaking planner/runtime consumers mid-migration and keeps each commit reversible and reviewable.
