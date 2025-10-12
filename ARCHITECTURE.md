# Laakhay TA - Technical Architecture

**Version**: 1.0  
**Status**: Living Document  
**Last Updated**: October 12, 2025

---

## Core Principles

`laakhay-ta` is a **stateless, pure-Python technical analysis engine** for deterministic, composable, exchange-agnostic computations.

### Architectural Tenets

1. **Stateless by Contract**: Class methods only, no instances, no state
2. **Deterministic**: Pure functions - same input → same output
3. **Composable**: DAG-based dependency resolution
4. **Multi-Asset Native**: Single timeframe, multi-symbol by default
5. **Zero Heavy Dependencies**: Only Pydantic for validation

---

## System Architecture

### Data Flow

```
ComputeRequest → Planner → DAG → Executor → TAOutput
                    ↓
              Data Adapter (fetch raw slices)
```

**Execution Steps**:
1. **Plan**: Resolve dependencies into DAG, topological sort
2. **Fetch**: Load minimal raw data per WindowSpec
3. **Execute**: Iterate DAG nodes, call compute(), cache results
4. **Return**: Target indicator's TAOutput

---

## Core Contracts

### BaseIndicator (base.py)

```python
class BaseIndicator(ABC):
    name: ClassVar[str]  # Unique identifier (e.g., "rsi")
    kind: ClassVar[Literal["batch", "stream"]] = "batch"
    
    @classmethod
    @abstractmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependencies (raw data + upstream indicators)."""
    
    @classmethod
    @abstractmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Pure function: TAInput + params → TAOutput. NO I/O, NO state."""
```

**Constraints**:
- ❌ No `__init__`, no instances
- ❌ No mutable class attributes
- ❌ No I/O or global state
- ✅ Pure computation only

---

### Dependency Specification (spec.py)

#### DataKind
```python
DataKind = Literal["price", "volume", "oi", "funding", "mark_price", "trades", "orderbook"]
```

#### WindowSpec
```python
class WindowSpec(BaseModel):
    lookback_bars: int = 0  # Historical bars needed
    min_lag_bars: int = 0   # Additional lag requirement
```

#### RawDataRequirement
```python
class RawDataRequirement(BaseModel):
    kind: DataKind
    price_field: Optional[PriceField] = None  # For kind="price"
    symbols: Optional[Sequence[str]] = None   # None = inherit
    window: WindowSpec = WindowSpec()
    only_closed: bool = True
```

#### IndicatorRef
```python
class IndicatorRef(BaseModel):
    name: str                                # Upstream indicator name
    params: Dict[str, Any] = {}              # Its parameters
    symbols: Optional[Sequence[str]] = None  # None = inherit
    window: WindowSpec = WindowSpec()
```

#### IndicatorRequirements
```python
class IndicatorRequirements(BaseModel):
    raw: list[RawDataRequirement] = []
    indicators: list[IndicatorRef] = []
```

---

### I/O Contracts (io.py)

#### TAInput (Engine → Indicator)
```python
class TAInput(BaseModel):
    candles: Mapping[str, Sequence[Candle]]  # Multi-symbol OHLCV
    oi: Optional[Mapping[str, Sequence[OIPoint]]] = None
    funding: Optional[Mapping[str, Sequence[FundingPoint]]] = None
    mark_price: Optional[Mapping[str, Sequence[MarkPricePoint]]] = None
    indicators: Optional[Mapping[Tuple[str, str, str], Any]] = None  # (name, hash, symbol)
    scope_symbols: Sequence[str]
    eval_ts: Optional[datetime] = None
```

#### TAOutput (Indicator → Engine)
```python
class TAOutput(BaseModel):
    name: str
    values: Mapping[str, Any]  # Per-symbol results (scalar/vector/dict)
    ts: Optional[datetime] = None
    meta: dict[str, Any] = {}
```

---

### Registry (registry.py)

```python
INDICATORS: Dict[str, Type[BaseIndicator]] = {}

def register(indicator_cls: Type[BaseIndicator]) -> None:
    """Register indicator class under its .name attribute."""

def get_indicator(name: str) -> Optional[Type[BaseIndicator]]:
    """Retrieve indicator class by name."""

def list_indicators() -> list[str]:
    """List all registered indicator names."""
```

---

### Planner (plan.py)

#### ComputeRequest
```python
class ComputeRequest(BaseModel):
    indicator_name: str
    params: Dict[str, Any] = {}
    symbols: Sequence[str]
    eval_ts: Optional[datetime] = None
```

#### ExecutionPlan
```python
class ExecutionPlan(BaseModel):
    nodes: List[PlanNode]  # Topologically sorted
```

#### Key Functions
```python
def stable_params_hash(params: Dict[str, Any]) -> str:
    """SHA256 hash of canonical JSON params (16 chars)."""

def build_execution_plan(req: ComputeRequest) -> ExecutionPlan:
    """Resolve dependencies into DAG, topological sort, detect cycles."""

def fetch_raw_slices(nodes: List[PlanNode]) -> Dict[Tuple, Any]:
    """Fetch minimal raw series per WindowSpec."""

def execute_plan(plan: ExecutionPlan, raw_cache: Dict) -> TAOutput:
    """Execute DAG: assemble TAInput, call compute(), cache results."""
```

**Algorithm** (build_execution_plan):
1. Get target indicator class from registry
2. Read `requirements()` recursively (DFS/BFS)
3. Build adjacency graph: node → [dependencies]
4. Topological sort (Kahn's algorithm)
5. Detect cycles → raise `CyclicDependencyError`
6. Return sorted nodes

---

## Data Models (models/)

### Candle (candle.py)
```python
class Candle(BaseModel):
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_closed: bool = True
    
    @property
    def hlc3(self) -> Decimal:
        """(high + low + close) / 3"""
    
    @property
    def ohlc4(self) -> Decimal:
        """(open + high + low + close) / 4"""
```

### OpenInterest, FundingRate, MarkPrice
```python
class OpenInterest(BaseModel):
    symbol: str
    timestamp: datetime
    open_interest: Decimal
    open_interest_value: Optional[Decimal] = None

class FundingRate(BaseModel):
    symbol: str
    timestamp: datetime
    rate: Decimal
    next_funding_time: Optional[datetime] = None

class MarkPrice(BaseModel):
    symbol: str
    timestamp: datetime
    mark_price: Decimal
    index_price: Optional[Decimal] = None
```

### Lightweight Time-Series Points (io.py)
```python
class OIPoint(BaseModel):
    ts: datetime
    oi: Decimal

class FundingPoint(BaseModel):
    ts: datetime
    rate: Decimal

class MarkPricePoint(BaseModel):
    ts: datetime
    price: Decimal
```

---

## Indicator Structure

### Directory Layout
```
laakhay/ta/indicators/
├── trend/            # SMA, EMA, Bollinger, etc.
├── momentum/         # RSI, MACD, Stochastic, etc.
├── volume/           # VWAP, OBV, Volume Profile
├── volatility/       # ATR, Standard Deviation
└── cross_asset/      # Correlation, Relative Strength
```

### Indicator Template
```python
from typing import ClassVar
from laakhay.ta.core import BaseIndicator, TAInput, TAOutput
from laakhay.ta.core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec

class ExampleIndicator(BaseIndicator):
    name: ClassVar[str] = "example"
    kind: ClassVar[Literal["batch", "stream"]] = "batch"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field="close",
                    window=WindowSpec(lookback_bars=14),
                    only_closed=True
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
            closes = [float(c.close) for c in candles[-period:]]
            value = sum(closes) / len(closes)
            results[symbol] = value
        
        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
            meta={"period": period}
        )

# Auto-register
from laakhay.ta.core.registry import register
register(ExampleIndicator)
```

---

## Operational Model

### 1. Request Phase
```python
request = ComputeRequest(
    indicator_name="rsi",
    params={"period": 14},
    symbols=["BTCUSDT", "ETHUSDT"],
    eval_ts=datetime(2025, 10, 12, 12, 0, 0, tzinfo=timezone.utc)
)
```

### 2. Planning Phase
```python
plan = build_execution_plan(request)
# Produces: ExecutionPlan(nodes=[raw_nodes..., indicator_nodes...])
```

### 3. Fetching Phase
```python
raw_cache = fetch_raw_slices(plan.nodes)
# Returns: {("price", "close", "BTCUSDT"): [Candle(...), ...], ...}
```

### 4. Execution Phase
```python
result = execute_plan(plan, raw_cache)
# Returns: TAOutput(name="rsi", values={"BTCUSDT": 65.3, ...}, ...)
```

---

## Error Handling

### Indicator Errors
```python
class InsufficientDataError(Exception):
    """Not enough data to compute indicator."""

class InvalidParameterError(Exception):
    """Invalid indicator params."""
```

**Best Practice**: Return empty `values` for symbols with insufficient data; raise for invalid params.

### Planner Errors
```python
class IndicatorNotFoundError(Exception):
    """Requested indicator not in registry."""

class CyclicDependencyError(Exception):
    """Dependency graph has cycles."""

class IncompatibleRequirementsError(Exception):
    """Requirements cannot be satisfied."""
```

---

## Testing Strategy

### Unit Tests (Per Indicator)
```python
def test_sma_correctness():
    candles = create_test_candles([10, 20, 30, 40, 50])
    input = TAInput(candles={"TEST": candles}, scope_symbols=["TEST"])
    output = SMAIndicator.compute(input, period=3)
    assert output.values["TEST"] == pytest.approx(40.0)  # (30+40+50)/3

def test_sma_determinism():
    candles = create_test_candles([...])
    input = TAInput(candles={"TEST": candles}, scope_symbols=["TEST"])
    result1 = SMAIndicator.compute(input, period=14)
    result2 = SMAIndicator.compute(input, period=14)
    assert result1 == result2
```

### Integration Tests (Planner)
```python
def test_plan_resolution():
    request = ComputeRequest(name="rsi", params={}, symbols=["BTC"])
    plan = build_execution_plan(request)
    assert plan.nodes[0].kind == "raw"
    assert plan.nodes[-1].kind == "indicator"

def test_cycle_detection():
    with pytest.raises(CyclicDependencyError):
        build_execution_plan(circular_request)
```

### Property-Based Tests
```python
from hypothesis import given, strategies as st

@given(prices=st.lists(st.floats(min_value=1.0, max_value=1e5), min_size=50))
def test_sma_properties(prices):
    """Property: SMA(period) <= max(prices[-period:])"""
    candles = create_candles_from_closes(prices)
    input = TAInput(candles={"TEST": candles}, scope_symbols=["TEST"])
    output = SMAIndicator.compute(input, period=20)
    if "TEST" in output.values:
        assert output.values["TEST"] <= max(prices[-20:])
```

---

## Performance Considerations

### Memory Optimization
- **WindowSpec Clipping**: Fetch only `lookback_bars + min_lag_bars`
- **Lazy Evaluation**: Only fetch data for `scope_symbols`
- **Slice Views**: Use `slice_tail(seq, n)` to avoid copying

### CPU Optimization
- **Caching**: Reuse outputs via `(name, params_hash, symbol)` keys
- **Topological Sort**: Compute each node once
- **Pure Python**: Profile first, optimize hotspots later with Numba/Cython

### Future: Parallelization
- **Per-Symbol**: Execute different symbols in parallel
- **DAG-Level**: Execute independent nodes concurrently
- **Constraint**: Stateless design enables trivial parallelization

---

## Security

### Input Validation
- Pydantic validators on all models
- Reject malformed data (negative prices, invalid symbols)
- Sanitize params before hashing

### Dependency Supply Chain
- Minimal dependencies (only Pydantic)
- Pin versions in `requirements.txt`
- Regular audits with `pip-audit`

### Data Integrity
- Immutable models (`frozen=True`)
- No mutation of `TAInput`
- Deterministic outputs enable audit trails

---

## Appendix: Glossary

- **Stateless**: No internal state; pure functions
- **Deterministic**: Same input → same output
- **Composable**: Combine/nest via dependency declarations
- **DAG**: Directed Acyclic Graph
- **WindowSpec**: Minimal historical context required
- **params_hash**: SHA-256 hash of canonicalized params
- **eval_ts**: Evaluation timestamp (last closed bar)

---

**End of Architecture Document**

*Living specification - update as project evolves.*
