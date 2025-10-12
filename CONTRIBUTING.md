# Contributing to Laakhay TA

Quick, technical guide for contributors. For detailed architecture, see `ARCHITECTURE.md`.

---

## Quick Start

```bash
# Setup
git clone https://github.com/YOUR_USERNAME/api.laakhay.com.git
cd api.laakhay.com/ta
python3.10 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Verify
make ci  # Must pass: lint, format, type-check, tests
```

---

## Core Architecture (30 seconds)

**Stateless, deterministic TA engine**: `compute(input, params) → output`

```python
class MyIndicator(BaseIndicator):
    name: ClassVar[str] = "my_indicator"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(raw=[...])  # Declare deps
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        # Pure math, no I/O, deterministic
        results = {}
        for symbol in input.scope_symbols:
            results[symbol] = calculate(input.candles[symbol], params)
        return TAOutput(name=cls.name, values=results)
```

**Key Contracts**:
- `TAInput`: Multi-asset candles + optional raw series (OI, funding)
- `TAOutput`: Per-symbol results + metadata
- `IndicatorRequirements`: Declarative deps (raw data + upstream indicators)

**Execution**: `Request → Planner (DAG) → Adapter (fetch) → Executor → Result`

---

## Non-Negotiable Rules

### 1. Stateless
❌ No `__init__`, no instances, no mutable class attributes, no global state  
✅ Only class methods, pure computation from inputs

### 2. Deterministic
❌ No `random()`, `datetime.now()`, I/O operations  
✅ Same `(input, params)` → same output, always

### 3. Type-Safe
❌ No `# type: ignore` without explanation  
✅ Full type hints, pass `mypy --strict`

### 4. No Heavy Deps
❌ No numpy, pandas, ta-lib  
✅ Only pydantic + stdlib

---

## Workflow

```bash
# 1. Create branch
git checkout -b feature/add-sma-indicator

# 2. Implement (see template below)

# 3. Test
make test        # 90%+ coverage required
make lint        # Ruff
make format      # Black
make type-check  # mypy
make ci          # All checks

# 4. Commit (Conventional Commits)
git commit -m "feat(indicators): add SMA indicator"

# 5. PR
# - All CI checks must pass
# - At least 1 maintainer approval
# - Squash and merge
```

---

## Adding an Indicator

**File**: `laakhay/ta/indicators/<category>/<name>.py`

```python
"""Simple Moving Average (SMA) indicator."""

from typing import ClassVar, Literal
from ...core import BaseIndicator, TAInput, TAOutput
from ...core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec
from ...core.utils import slice_tail

class SMAIndicator(BaseIndicator):
    """Simple Moving Average. Computes mean of last N closes."""
    
    name: ClassVar[str] = "sma"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(
            raw=[RawDataRequirement(
                kind="price",
                price_field="close",
                window=WindowSpec(lookback_bars=200),
                only_closed=True,
            )]
        )
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        period = params.get("period", 20)
        if period < 1:
            raise ValueError(f"period must be >= 1, got {period}")
        
        results = {}
        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if len(candles) < period:
                continue  # Skip if insufficient data
            
            recent = slice_tail(candles, period)
            closes = [float(c.close) for c in recent]
            results[symbol] = sum(closes) / len(closes)
        
        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={"period": period},
        )

from ...core.registry import register
register(SMAIndicator)
```

**Tests**: `tests/unit/indicators/test_sma.py`

```python
import pytest
from laakhay.ta.core import TAInput
from laakhay.ta.indicators.trend import SMAIndicator

def test_sma_correctness(sample_candles):
    input = TAInput(candles={"TEST": sample_candles}, scope_symbols=["TEST"])
    output = SMAIndicator.compute(input, period=3)
    assert output.values["TEST"] == pytest.approx(expected)

def test_sma_determinism(sample_candles):
    input = TAInput(candles={"TEST": sample_candles}, scope_symbols=["TEST"])
    r1 = SMAIndicator.compute(input, period=3)
    r2 = SMAIndicator.compute(input, period=3)
    assert r1.values == r2.values

def test_sma_insufficient_data():
    short = create_candles([1, 2])
    input = TAInput(candles={"TEST": short}, scope_symbols=["TEST"])
    output = SMAIndicator.compute(input, period=10)
    assert "TEST" not in output.values

def test_sma_invalid_params(sample_candles):
    input = TAInput(candles={"TEST": sample_candles}, scope_symbols=["TEST"])
    with pytest.raises(ValueError):
        SMAIndicator.compute(input, period=-1)
```

---

## Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

**Scopes**: `core`, `indicators`, `models`, `signals`, `adapters`, `tests`, `ci`, `docs`

**Examples**:
```
feat(indicators): add SMA indicator

Implement Simple Moving Average with period parameter.
Includes validation and tests.

Closes #42
```

```
fix(core): validate WindowSpec lookback_bars >= 0

Fixes #123
```

---

## Code Style

```bash
# Auto-fix
make format  # Black (line length 100)
make lint    # Ruff

# Type check
make type-check  # mypy --strict
```

**Import order**: stdlib → pydantic → local relative

**Docstrings**: Google-style, include params and returns

**Naming**: `PascalCase` (classes), `snake_case` (functions), `UPPER_SNAKE` (constants)

---

## Common Pitfalls

### ❌ DON'T
```python
# Mutable defaults
def compute(cls, input, symbols=[]):  # ❌

# Mutate input
input.candles["BTC"].append(...)  # ❌

# Global state
CACHE = {}
cls.compute(...): CACHE[...] = ...  # ❌

# I/O
with open("data.csv") as f: ...  # ❌
```

### ✅ DO
```python
# Immutable defaults
def compute(cls, input, symbols=None):  # ✅
    if symbols is None: symbols = []

# Read only
candles = input.candles.get("BTC", [])  # ✅

# Pure computation
result = calculate(input.candles, params)  # ✅

# Handle edge cases
if len(candles) < period:
    continue  # Skip, don't crash
```

---

## Testing Requirements

- **Unit tests**: All new functions/classes
- **Determinism tests**: All indicators
- **Edge cases**: Insufficient data, invalid params
- **Coverage**: 90%+ minimum, 95%+ goal

```bash
make test              # Run with coverage
open htmlcov/index.html  # View report
```

---

## Documentation

Update when adding:
- **New indicator**: README.md examples
- **New API**: ARCHITECTURE.md contracts
- **Breaking change**: MIGRATION.md

---

## Questions?

- 📖 Docs: `DOCS_INDEX.md`
- 💬 Discussions: GitHub Discussions  
- 🐛 Issues: GitHub Issues

**Read**: `STATUS.md` (current state) → `ARCHITECTURE.md` (design) → `PLANS.md` (roadmap)

---

## License

By contributing, you agree your contributions are licensed under MIT License.
