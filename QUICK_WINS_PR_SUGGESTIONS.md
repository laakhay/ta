# Quick-Win PRs to Strengthen `laakhay-ta` (Backend-Friendly, Backend-Agnostic)

The following PR ideas focus on building robust expression/indicator capabilities **inside `laakhay-ta`** so any consumer (backend, CLI, batch jobs) can rely on a consistent library surface. None of these PRs introduce backend-specific logic—they simply expose TA features the backend can adopt.

---

## 1. 🚀 Ship `ta.expr.preview` (End-to-End Expression Runner)

**Impact**: Highest – Gives every consumer a single API to parse, compile, and evaluate expressions with consistent trimming/trigger extraction.

- **What**: Create `laakhay/ta/expr/preview.py` that accepts `expression_text | StrategyExpression`, optional raw bars or an existing `Dataset`, symbol/timeframe, and returns `{series, triggers, indicators, trim}`.
- **How**:
  - Reuse `ta.strategy.parse_expression_text`, `compile_expression`, `compute_trim`, and `laakhay.ta.dataset` helpers to normalize inputs.
  - Encapsulate result normalization (the “find the right Series in dict outputs” logic) so callers no longer replicate it.
  - Add tests that simulate the current backend preview cases (missing symbol/timeframe, invalid expressions, boolean triggers).
- **Files to touch**: new `laakhay/ta/expr/__init__.py`, `laakhay/ta/expr/preview.py`, tests under `tests/expr/test_preview.py`.

---

## 2. ✅ Add `ta.expr.validate` (Syntax + Registry Validation)

**Impact**: High – replaces ad-hoc backend validation with a canonical TA routine.

- **What**: A validation API that parses expression text, enumerates indicators, verifies each against the registry (including `select` field whitelist), and attempts a dry-run compile.
- **How**:
  - Move the validation logic currently mirrored in `backend/src/services/strategy/__init__.py:217+` into TA, but generalize results (return `errors`, `warnings`, `indicators`, `valid`).
  - Provide structured exception types (e.g., `ExprValidationError`) for consumers to turn into HTTP errors or CLI messages.
  - Include tests for bad indicator names, invalid select fields, nested expressions, etc.
- **Files**: `laakhay/ta/expr/validate.py`, registry helpers, tests in `tests/expr/test_validate.py`.

---

## 3. 📚 Expose Indicator Catalog + Parameter Coercion in TA

**Impact**: High – lets any consumer build indicator browsers or execute indicators without duplicating reflection logic.

- **What**: Relocate the backend’s `CatalogBuilder`, `TypeParser`, `ParameterParser`, and `OutputSerializer` equivalents into `laakhay-ta` (e.g., new `laakhay/ta/catalog` package).
- **How**:
  - Build descriptors straight from `registry.registry.get_global_registry()`.
  - Provide `describe_indicator(name)`, `list_indicator_catalog()`, `coerce_params(descriptor, raw_params)`, and `serialize_outputs(...)` helpers.
  - Maintain JSON-friendly serialization utilities (currently `backend/src/services/ta/utils.py`).
- **Files**: `laakhay/ta/catalog/__init__.py`, `catalog/builder.py`, `catalog/params.py`, `catalog/output.py`, tests covering a handful of built-in indicators.

---

## 4. 📈 Implement `ta.expr.analyze` (Lookback + Requirement Insights)

**Impact**: Medium-High – centralizes the “how many bars do we need?” logic used by alert services and data planners.

- **What**: Build an analyzer that returns indicator nodes, computed trim, estimated period parameters, and recommended safety buffers.
- **How**:
  - Wrap `IndicatorAnalyzer.collect`/`compute_trim` with additional heuristics (scan `period`/`length` params).
  - Return a structured payload (`{"indicators": [...], "lookback": N, "min_bars": N + buffer, "max_period": ...}`).
  - Cover cases with nested expressions, select nodes, and missing metadata in tests.
- **Files**: `laakhay/ta/expr/analyze.py`, tests in `tests/expr/test_analyze.py`.

---

## 5. 🧰 Publish Dataset & Result Normalization Utilities

**Impact**: Medium – removes the need for consumers to guess how to trim datasets or interpret expression results.

- **What**:
  - Offer `dataset_from_bars` + `trim_dataset` wrappers (currently already in `ta.dataset`) via a stable `ta.expr.dataset` helper that pairs with preview/validate APIs.
  - Provide a `ta.expr.result` module with utilities like `ensure_series(expression_result, symbol, timeframe)` and `extract_triggers(series)`.
- **How**:
  - Factor the backend’s defensive result parsing into reusable TA functions with clear error messages.
  - Document the expected return structures so consumers know how to extend them.
- **Files**: `laakhay/ta/expr/dataset.py`, `laakhay/ta/expr/result.py`, unit tests mirroring backend edge cases (dict outputs, missing series, scalar results).

---

Delivering the five PRs above makes `laakhay-ta` a complete expression platform. The backend (and any future consumer) can simply adapt HTTP requests around these APIs without embedding TA-specific logic, achieving the robustness goal without coupling layers.
