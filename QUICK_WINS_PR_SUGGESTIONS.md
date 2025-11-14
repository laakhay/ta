# Quick-Win PRs to Strengthen `laakhay-ta` (Backend-Friendly, Backend-Agnostic)

The following PR ideas focus on building robust expression/indicator capabilities **inside `laakhay-ta`** so any consumer (backend, CLI, batch jobs) can rely on a consistent library surface. None of these PRs introduce backend-specific logic—they simply expose TA features the backend can adopt.

---

## ✅ Completed PRs

- **PR 1**: Replace `importlib.reload` with Proper Lazy Loading
- **PR 2**: Ship `ta.expr.preview` (End-to-End Expression Runner)
- **PR 3**: Add `ta.expr.validate` (Syntax + Registry Validation)
- **PR 4**: Expose Indicator Catalog + Parameter Coercion in TA

---

## 1. 📈 Implement `ta.expr.analyze` (Lookback + Requirement Insights)

**Impact**: Medium-High – centralizes the "how many bars do we need?" logic used by alert services and data planners.

- **What**: Build an analyzer that returns indicator nodes, computed trim, estimated period parameters, and recommended safety buffers.
- **How**:
  - Wrap `IndicatorAnalyzer.collect`/`compute_trim` with additional heuristics (scan `period`/`length` params).
  - Return a structured payload (`{"indicators": [...], "lookback": N, "min_bars": N + buffer, "max_period": ...}`).
  - Cover cases with nested expressions, select nodes, and missing metadata in tests.
- **Files**: `laakhay/ta/expr/analyze.py`, tests in `tests/expr/test_analyze.py`.

---

## 2. 🧰 Publish Dataset & Result Normalization Utilities

**Impact**: Medium – removes the need for consumers to guess how to trim datasets or interpret expression results.

- **What**:
  - Offer `dataset_from_bars` + `trim_dataset` wrappers (currently already in `ta.dataset`) via a stable `ta.expr.dataset` helper that pairs with preview/validate APIs.
  - Provide a `ta.expr.result` module with utilities like `ensure_series(expression_result, symbol, timeframe)` and `extract_triggers(series)`.
- **How**:
  - Factor the backend's defensive result parsing into reusable TA functions with clear error messages.
  - Document the expected return structures so consumers know how to extend them.
- **Files**: `laakhay/ta/expr/dataset.py`, `laakhay/ta/expr/result.py`, unit tests mirroring backend edge cases (dict outputs, missing series, scalar results).

---

Delivering the remaining PRs above completes the `laakhay-ta` expression platform. The backend (and any future consumer) can simply adapt HTTP requests around these APIs without embedding TA-specific logic, achieving the robustness goal without coupling layers.
