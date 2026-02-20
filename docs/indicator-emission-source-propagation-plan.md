# Indicator Emission and Source Propagation Plan (TA -> Kendra -> Frontend)

## Problem

Expression-derived indicators are not emitted with enough semantic context for rendering decisions.

Example:
- Expression: `sma(volume, 50)`
- Current gap: frontend receives a generic `sma` indicator without reliable input provenance (`volume` vs `close`), so placement defaults are heuristic and can be wrong.

This causes:
- Wrong pane placement (overlay vs pane, price vs volume context)
- Ad-hoc backend hacks (special-casing `volume` in chart route)
- Drift between TA runtime truth and chart-feed payload representation

## Current State (Concrete)

### TA
- `preview()` returns:
  - `indicators`: AST indicator nodes
  - `indicator_series`: `dict[str, Series]` keyed as `"{name}_{node_id}"`
- It does **not** return a first-class emitted indicator contract with:
  - stable key identity per output
  - resolved input binding/source lineage
  - pane/render hints

Relevant files:
- `ta/laakhay/ta/expr/runtime/preview.py`
- `ta/laakhay/ta/expr/dsl/nodes.py`
- `ta/laakhay/ta/expr/planner/builder.py`
- `ta/laakhay/ta/registry/schemas.py`

### Kendra
- `chart-feed` derived mode currently:
  - calls strategy preview
  - then re-evaluates derived indicators as explicit indicator calls
  - includes a brittle rule for volume input:
    - if `input_expr.field == "volume"`, inject `params["source"] = "volume"`

Relevant files:
- `kendra/src/services/strategy/__init__.py`
- `kendra/src/app/routes/api/v1/market_data/chart.py`

### Frontend
- Placement is mostly inferred by indicator name (`PANE_INDICATORS`) rather than source-aware metadata.

Relevant files:
- `prangan/src/core/chart/utils/indicator-snapshot.ts`
- `prangan/src/core/chart/core/constants.ts`
- `prangan/src/types/strategy.ts`

## Target Outcome

For every emitted indicator output, TA should produce structured metadata that Kendra forwards unchanged, allowing frontend placement/rendering without heuristics.

Specifically:
- `sma(volume, 50)` is tagged as volume-derived
- `sma(close, 50)` is tagged as price-derived
- `sma(BTC.trades.volume, 50)` is tagged with source=`trades`, field=`volume`
- Multi-output indicators (`macd`) emit per-output keys + role metadata

## Proposed Contract (Additive First)

Add a new emitted object in TA preview: `indicator_emissions`.

Each entry should represent one **output series** (not just one indicator node):

```json
{
  "key": "i12_signal",
  "node_id": 12,
  "indicator": "macd",
  "output": "signal",
  "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
  "input_expr": {"type": "indicator", "name": "sma", "params": {"period": 20}},
  "input_binding": {
    "source": "ohlcv",
    "field": "close",
    "symbol": null,
    "timeframe": null,
    "exchange": null
  },
  "render": {
    "role": "signal",
    "pane_hint": "pane",
    "style_hint": "line"
  },
  "series": [
    {"timestamp": "2026-01-01T00:00:00Z", "value": 1.23}
  ]
}
```

Notes:
- Keep legacy `indicators` and `indicator_series` temporarily for compatibility.
- `pane_hint` should be one of:
  - `price_overlay`
  - `volume`
  - `pane`

## Input Binding Resolution Rules

Deterministic precedence for resolving indicator input source/field:

1. `IndicatorNode.input_expr` (explicit expression input)
2. indicator params that select field/source (e.g. `field`, `source`)
3. registry metadata defaults (`metadata.input_field`, `required_fields`)
4. fallback to `ohlcv.close`

For `input_expr`, recursively resolve to a dominant leaf binding:
- `AttributeNode` -> direct source binding
- `IndicatorNode` -> inherit dominant binding of its input
- `BinaryNode` of mixed sources -> mark as mixed:
  - `input_binding.field = "mixed"`
  - `pane_hint = "pane"` (safe default)

## Pane/Render Hint Rules in TA

Use descriptor output metadata + resolved input binding:

1. If output metadata has `role=histogram` -> `style_hint=histogram`
2. If category/indicator is oscillator-like (`macd`, `rsi`, `stochastic`, etc.) -> `pane_hint=pane`
3. Else if dominant input field is `volume` -> `pane_hint=volume`
4. Else -> `pane_hint=price_overlay`

Important: keep these rules centralized in TA, not replicated in Kendra/frontend.

## Implementation Plan

### Phase 1: TA Runtime Emission Model

1. Create runtime emission models in TA:
   - `IndicatorInputBinding`
   - `IndicatorRenderHints`
   - `IndicatorEmission`
2. Extend `PreviewResult` with `indicator_emissions: list[IndicatorEmission]`.
3. Build emissions in `preview()` by walking plan graph indicator nodes and joining with node outputs.
4. Derive `node_id` from planner graph directly (already available).
5. Keep existing `indicators` and `indicator_series` unchanged.

Files:
- `ta/laakhay/ta/expr/runtime/preview.py`
- new helper module (recommended): `ta/laakhay/ta/expr/runtime/emission.py`

### Phase 2: TA Tests

Add focused tests for emission semantics:

1. `sma(volume, 50)` -> `input_binding.field=volume`, `pane_hint=volume`
2. `sma(close, 50)` -> `input_binding.field=close`, `pane_hint=price_overlay`
3. `sma(BTC.trades.volume, 10)` -> `input_binding.source=trades`
4. `crossup(ema(10), ema(20))` -> both EMA emissions present with stable keys
5. `macd(close)` -> 3 emissions (`macd`, `signal`, `histogram`) with output roles
6. Mixed input example (`sma(close + volume, 10)`) -> `mixed` binding, `pane_hint=pane`

Files:
- `ta/tests/unit/expr/runtime/test_preview.py`
- optionally new: `ta/tests/unit/expr/runtime/test_emission.py`

### Phase 3: Kendra Pass-Through (No Re-Inference)

1. Add new fields to strategy preview response schema for emitted indicators.
2. In `StrategyService.preview`, map TA emissions directly to domain schema.
3. In `chart-feed` derived mode:
   - stop inferring source from `input_expr.field`
   - stop special-casing `params.source = "volume"`
   - consume emitted series/hints directly from strategy preview
4. Keep old chart payload fields for compatibility during transition.

Files:
- `kendra/src/domain/strategy/schemas.py`
- `kendra/src/services/strategy/__init__.py`
- `kendra/src/app/routes/api/v1/market_data/chart.py`

### Phase 4: Frontend Adoption

1. Extend frontend types for new metadata:
   - `pane_hint`, `input_binding`, `render.role/style_hint`
2. Update indicator placement logic:
   - prefer server `pane_hint`
   - fallback to local heuristic only if missing
3. Remove/retire name-only pane assumptions where possible.

Files:
- `prangan/src/types/strategy.ts`
- `prangan/src/types/indicators.ts`
- `prangan/src/core/chart/utils/indicator-snapshot.ts`

### Phase 5: Cleanup

After frontend is fully switched:
1. Remove duplicate derived re-computation path in `chart-feed`.
2. Remove temporary compatibility glue fields if no clients depend on them.

## API Versioning and Rollout Strategy

Use additive rollout to avoid breaking existing clients:

1. Add new fields first (TA + Kendra)
2. Frontend reads new fields with fallback
3. Remove old behavior only after frontend release is stable

## Risks and Mitigations

1. Risk: mixed-source expressions are ambiguous for pane selection
- Mitigation: explicit `mixed` binding + `pane` fallback

2. Risk: key instability across expression changes
- Mitigation: keys based on planner `node_id` + output name, documented as request-scoped identity

3. Risk: payload size growth
- Mitigation: keep emission metadata compact; if needed, add optional `include_indicator_emissions` flag later

4. Risk: divergence between preview and chart-feed paths
- Mitigation: chart-feed should consume strategy preview emissions directly, not re-derive

## Definition of Done

1. `sma(volume, 50)` renders in volume context without frontend guessing.
2. No backend special-cases for volume source inference in chart route.
3. Multi-output indicators render with correct roles from metadata.
4. TA + Kendra + frontend tests cover explicit source and mixed-source cases.
5. Legacy payload compatibility preserved during migration window.

## Suggested Execution Order

1. TA emission model + tests
2. Kendra schema + pass-through wiring
3. Frontend type + placement migration
4. Remove chart-feed derived recomputation heuristics

