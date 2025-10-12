# Laakhay TA - Quick Reference Card

**Version**: 1.0 | **Date**: Oct 12, 2025 | **Status**: 30% Complete

---

## 📍 Current State

```
✅ DONE: Core contracts, data models, architecture docs
⚠️  TODO: Planner implementation (CRITICAL PATH)
⚠️  TODO: Indicator library (BLOCKING)
❌ TODO: Test suite, CI/CD, examples
```

**Next Action**: Start Phase 1 (Testing Infrastructure) from `PLANS.md`

---

## 📚 Document Quick Access

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **DOCS_INDEX.md** | Navigation hub | Start here |
| **STATUS.md** | What exists, what's missing | First read |
| **ARCHITECTURE.md** | Technical spec | Before coding |
| **PLANS.md** | Step-by-step roadmap | During coding |
| README.md | User guide | For context |

---

## 🏗️ Core Architecture (30 Second Version)

### The Big Idea
Pure, stateless technical analysis: `compute(input, params) → output`

### Key Contracts

```python
# 1. Indicator (stateless class)
class MyIndicator(BaseIndicator):
    name = "my_indicator"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(raw=[...])  # Declare deps
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        # Pure math, no I/O, deterministic
        return TAOutput(name="...", values={...})

# 2. Input (multi-asset, single timeframe)
TAInput(
    candles={"BTCUSDT": [...], "ETHUSDT": [...]},
    scope_symbols=["BTCUSDT", "ETHUSDT"],
    eval_ts=datetime(...),
)

# 3. Output (per-symbol results)
TAOutput(
    name="sma",
    values={"BTCUSDT": 42000.5, "ETHUSDT": 2500.3},
    ts=datetime(...),
)
```

### Execution Flow
```
User → Request → Planner (DAG) → Adapter (fetch) → Executor → Result
                    ↓
            Build dependency graph
            Topological sort
            Detect cycles
```

---

## 🎯 Implementation Priorities

### Week 1: Testing (Phase 1)
```bash
# Create tests/
# Add pytest fixtures
# Write unit tests for core/
# Setup CI/CD (GitHub Actions)
```
**Goal**: 90%+ coverage, all tests passing

### Week 2: Planner (Phase 2)
```bash
# Implement build_execution_plan()
# Add cycle detection
# Implement execute_plan()
# Create DataAdapter interface
```
**Goal**: Can execute simple indicators

### Week 3: Indicators (Phase 3)
```bash
# SMA, EMA (trend)
# RSI (momentum)
# MACD (composite)
# VWAP (volume)
```
**Goal**: 5 production-ready indicators

### Week 4: Polish (Phase 5)
```bash
# End-to-end examples
# API docs
# Tutorials
# README updates
```
**Goal**: User-ready library

---

## 💡 Key Design Principles

1. **Stateless**: No `__init__`, no instances, no internal state
2. **Deterministic**: Same input → same output, always
3. **Composable**: Indicators depend on indicators (DAG)
4. **Pure**: No I/O, no side effects, no global mutation
5. **Typed**: Full Pydantic validation, mypy strict

---

## 🚀 Quick Start (Developer)

```bash
# 1. Setup
cd /path/to/laakhay/ta
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Read docs
cat STATUS.md        # What exists
cat ARCHITECTURE.md  # Design
cat PLANS.md         # Roadmap

# 3. Start Phase 1
mkdir -p tests/unit/core
# Follow PLANS.md § Commit 1.1

# 4. Run checks
make test
make lint
make type-check
make ci
```

---

## 📊 Critical Path

```
Tests → Planner → Indicators → MVP
  ↓        ↓          ↓
Week 1   Week 2    Week 3
```

**Blockers**:
- ⚠️ Planner not implemented (CRITICAL)
- ⚠️ Indicators empty (CRITICAL)
- ⚠️ No tests (HIGH)

**Non-Blockers**:
- Examples incomplete (can wait)
- Signals module empty (future)
- Multi-timeframe (future)

---

## 🔧 Essential Commands

```bash
# Testing
make test              # Run pytest with coverage
make test-unit         # Unit tests only (after created)
make test-integration  # Integration tests (after created)

# Code Quality
make lint              # Ruff linting
make format            # Black formatting
make format-check      # Check formatting
make type-check        # Mypy type checking

# All Checks
make ci                # Run all checks (CI equivalent)

# Cleanup
make clean             # Remove build artifacts
```

---

## 📐 Code Templates

### Adding a New Indicator
```python
# laakhay/ta/indicators/<category>/<name>.py

from typing import ClassVar, Literal
from ...core import BaseIndicator, TAInput, TAOutput
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec

class MyIndicator(BaseIndicator):
    """Indicator description."""
    
    name: ClassVar[str] = "my_indicator"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field="close",
                    window=WindowSpec(lookback_bars=50),
                )
            ]
        )
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        period = params.get("period", 14)
        results = {}
        
        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if len(candles) < period:
                continue
            
            # === PURE MATH HERE ===
            value = ...  # Your calculation
            results[symbol] = value
        
        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={"period": period},
        )

# Auto-register
from ...core.registry import register
register(MyIndicator)
```

### Writing Tests
```python
# tests/unit/indicators/test_my_indicator.py

import pytest
from laakhay.ta.indicators.<category> import MyIndicator
from laakhay.ta.core import TAInput

def test_my_indicator_correctness(sample_candles):
    """Test indicator produces correct values."""
    input = TAInput(candles={"TEST": sample_candles}, scope_symbols=["TEST"])
    output = MyIndicator.compute(input, period=5)
    assert output.values["TEST"] == pytest.approx(42.0)

def test_my_indicator_determinism(sample_candles):
    """Test indicator is deterministic."""
    input = TAInput(candles={"TEST": sample_candles}, scope_symbols=["TEST"])
    result1 = MyIndicator.compute(input, period=5)
    result2 = MyIndicator.compute(input, period=5)
    assert result1.values == result2.values

def test_my_indicator_insufficient_data():
    """Test indicator handles insufficient data."""
    # ... test with len(candles) < period
```

---

## 🎓 Learning Resources

### Internal Docs
- `ARCHITECTURE.md` § Core Contracts → Interface specifications
- `ARCHITECTURE.md` § Operational Model → How execution works
- `PLANS.md` § Phase 2 → Planner implementation details
- `PLANS.md` § Phase 3 → Indicator examples

### External References
- Pydantic docs: https://docs.pydantic.dev
- pytest docs: https://docs.pytest.org
- Technical Analysis: Investopedia, TradingView docs

---

## ⚠️ Common Pitfalls

1. **Don't** use instances of `BaseIndicator` (use class methods only)
2. **Don't** do I/O in `compute()` (pure computation only)
3. **Don't** mutate `TAInput` (it's immutable)
4. **Don't** store state in indicators (stateless by design)
5. **Do** validate params in `compute()` (raise clear errors)
6. **Do** handle insufficient data gracefully (skip symbol, don't crash)
7. **Do** write determinism tests (same input → same output)

---

## 📞 Getting Help

1. **Stuck on architecture?** → Read `ARCHITECTURE.md` relevant section
2. **Don't know what to build?** → Follow `PLANS.md` step-by-step
3. **Want big picture?** → Read `STATUS.md` and `DOCS_INDEX.md`
4. **Bug or question?** → GitHub Issues
5. **Feature idea?** → GitHub Discussions

---

## 📈 Success Indicators

- ✅ All tests passing (`make test`)
- ✅ No linting errors (`make lint`)
- ✅ No type errors (`make type-check`)
- ✅ >90% test coverage
- ✅ All indicators deterministic
- ✅ Documentation up to date

---

**TL;DR**: Read `STATUS.md`, then follow `PLANS.md` Phase 1 → 2 → 3. Ask questions early. Test everything.

---

**Document Version**: 1.0  
**Last Updated**: October 12, 2025  
**Next Review**: After Phase 1 completion
