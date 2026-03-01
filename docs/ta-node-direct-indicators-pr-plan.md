# TA-Node Direct Indicators (Rust -> TypeScript) PR Plan

## Goal
Expose direct indicator calls from `ta-engine` to TypeScript via `ta-node`, with no DSL/planner layer.

## Scope
- In scope:
  - Thin Node bindings for direct indicator functions.
  - Typed TS API for function signatures and tuple outputs.
  - Minimal runtime validation for argument length/period sanity.
  - High-signal parity tests against `ta-engine` behavior.
- Out of scope:
  - Expression DSL/planner in Node.
  - Dataset/graph execution runtime in Node.
  - Drishya integration work.

## API Shape (V1)
Use direct function calls, mirroring Rust naming/params where practical:
- Single output: `rsi`, `sma`, `ema`, `wma`, `hma`, `atr`, `obv`, `vwap`, `cmf`, `cci`, `roc`, `cmo`, `mfi`
- Multi output tuples as objects in TS:
  - `macd -> { macd, signal, histogram }`
  - `bbands -> { upper, middle, lower }`
  - `stochastic -> { k, d }`
  - `adx -> { adx, plusDi, minusDi }`
  - `ichimoku -> { tenkanSen, kijunSen, senkouSpanA, senkouSpanB, chikouSpan }`
  - `supertrend -> { supertrend, direction }`
  - `psar -> { sar, direction }`
  - `swingPointsRaw -> { swingHigh, swingLow }`
  - `vortex -> { plus, minus }`

## Binding Strategy
Preferred: `napi-rs` in `crates/ta-node`.
- Keep wrappers very thin over `ta_engine::*` calls.
- Convert Rust tuples into JS objects for stable ergonomic TS API.
- Use one central validator for common checks (`period > 0`, same-length arrays where required).

## Commit-by-Commit Plan

### Commit 1: Setup `ta-node` as real Node addon crate
Message:
- `feat(node): bootstrap napi-rs addon for ta-node`

Touchpoints:
- `crates/ta-node/Cargo.toml`
- `crates/ta-node/src/lib.rs`
- `crates/ta-node/package.json` (new)
- `crates/ta-node/build.rs` (if needed by chosen napi setup)
- `crates/ta-node/README.md`
- `crates/ta-node/index.d.ts` (new initial types)

Changes:
- Add `napi`/`napi-derive` dependencies and crate type for Node addon.
- Replace scaffold export with `engineVersion()` function for smoke wiring.
- Add JS package metadata + scripts for local build/test.

Tests (minimal/potent):
- Rust unit test: version export returns non-empty string.
- Node smoke test: require/import module and call `engineVersion()`.

Acceptance:
- `cargo check -p ta-node` passes.
- Node smoke test passes.

---

### Commit 2: Core MA + momentum single-series endpoints
Message:
- `feat(node): expose core direct indicators for single-series inputs`

Touchpoints:
- `crates/ta-node/src/lib.rs` (or split into `api/base.rs`)
- `crates/ta-node/index.d.ts`
- `crates/ta-node/test/smoke.spec.ts` (new)

Functions:
- `sma`, `ema`, `wma`, `hma`, `rsi`, `roc`, `cmo`

Changes:
- Add thin wrappers with period validation.
- TS signatures return `number[]`.

Tests:
- TS test: each function returns array of same length as input.
- TS test: invalid period (`0`) throws.
- Optional parity micro-check: `sma([1,2,3,4],2)` expected `[NaN,1.5,2.5,3.5]` pattern.

Acceptance:
- New functions callable from TS and typed.

---

### Commit 3: OHLC/volume single-output endpoints
Message:
- `feat(node): add direct ohlc-volume indicators`

Touchpoints:
- `crates/ta-node/src/lib.rs`
- `crates/ta-node/index.d.ts`
- `crates/ta-node/test/ohlcv.spec.ts` (new)

Functions:
- `atr`, `obv`, `vwap`, `cmf`, `cci`, `mfi`, `klingerVf`

Changes:
- Add shared length checks for OHLCV arrays.
- Keep wrapper logic minimal and deterministic.

Tests:
- Mismatched lengths throw clear errors.
- Output length equals input length.
- One deterministic fixture for `obv` and `vwap` with exact expected values.

Acceptance:
- OHLCV endpoints are stable and typed.

---

### Commit 4: Multi-output direct endpoints (tuple->object mapping)
Message:
- `feat(node): expose multi-output indicators with typed object returns`

Touchpoints:
- `crates/ta-node/src/lib.rs`
- `crates/ta-node/index.d.ts`
- `crates/ta-node/test/multi_output.spec.ts` (new)

Functions:
- `macd`, `bbands`, `stochastic`, `adx`, `ichimoku`, `supertrend`, `psar`, `vortex`, `swingPointsRaw`, `elderRay`, `fisher`, `donchian`, `keltner`

Changes:
- Map Rust tuple outputs to JS object fields with explicit names.
- Normalize naming in TS (`plusDi`, `minusDi`, etc.) while preserving semantic parity.

Tests:
- For each multi-output endpoint: assert required keys exist.
- Assert each returned series length equals input length.
- One precise value fixture each for `macd` and `bbands` on tiny deterministic dataset.

Acceptance:
- All planned multi-output indicators available via object-return API.

---

### Commit 5: Error model hardening and docs/examples
Message:
- `refactor(node): standardize validation errors and add usage docs`

Touchpoints:
- `crates/ta-node/src/lib.rs`
- `crates/ta-node/README.md`
- `crates/ta-node/index.d.ts`
- `docs/api/index.mdx` (optional pointer)

Changes:
- Standardize errors: `ERR_PERIOD_INVALID`, `ERR_LENGTH_MISMATCH` messages.
- README includes direct usage examples for 5-6 key indicators.
- Clarify NaN warmup behavior in docs.

Tests:
- TS tests assert error message/code consistency.

Acceptance:
- Stable and documented error behavior.

---

### Commit 6: Minimal parity harness vs Rust/Python references
Message:
- `test(node): add parity fixtures for direct indicator bindings`

Touchpoints:
- `crates/ta-node/test/fixtures/*.json` (new)
- `crates/ta-node/test/parity.spec.ts` (new)
- Optional helper script for fixture generation from Rust/Python.

Changes:
- Add compact fixtures for representative indicators:
  - `sma`, `rsi`, `macd`, `bbands`, `atr`, `adx`, `stochastic`, `obv`
- Compare output arrays with tolerance for floats, explicit NaN handling.

Tests:
- A small set of deterministic parity snapshots.

Acceptance:
- TS addon output aligned with core engine expectations for key indicators.

## Test Matrix (Minimal But Strong)
- Input validation:
  - period zero
  - mismatched array lengths
- Shape invariants:
  - output lengths
  - tuple/object key presence
- Numerical confidence:
  - exact values for tiny deterministic samples where practical
  - tolerance-based parity for longer series

## Quality Gate Per Commit
Run before each commit:
1. `cargo fmt --all --check`
2. `cargo clippy --workspace --all-targets -- -D warnings`
3. `cargo test -p ta-node`
4. Node test command (e.g. `npm test` in `crates/ta-node`)

## Suggested Implementation Order for First Working Slice
If we want a very fast first end-to-end usable result:
1. Commit 1
2. Commit 2 with only `sma`, `ema`, `rsi`, `macd`, `bbands`
3. Commit 4 partial for `macd`/`bbands` object returns
Then expand through commits 3/4/6.

## Non-Goals Guardrail
Do not add planner/dsl abstractions in `ta-node` for this PR series.
Keep the boundary direct, function-per-indicator, and thin over `ta-engine`.
