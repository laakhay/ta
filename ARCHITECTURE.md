# Laakhay TA - Architecture

**Version**: 2.0 | **Status**: v0.1.0 Foundation (80%) | **Updated**: Oct 12, 2025

---

## Design Principles

**Stateless** · **Deterministic** · **Composable** · **Dependency-Aware** · **Series-First**

Pure functions (input → output). No internal state. DAG-based dependency resolution. Minimal coupling via adapters.

---

## System Flow

```
ComputeRequest → build_execution_plan() → ExecutionPlan → fetch_raw_slices() → execute_plan() → TAOutput
```

1. **Plan**: Resolve dependencies to DAG, topological sort
2. **Fetch**: Get minimal data per WindowSpec
3. **Execute**: Run nodes in order, cache outputs

---

## Core Contracts

### BaseIndicator (core/base.py)

```python
class BaseIndicator(BaseModel):
    name: ClassVar[str]  # Unique identifier
    kind: ClassVar[Literal["batch", "stream"]] = "batch"
    
    @classmethod
    @abstractmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare raw data + upstream indicator dependencies."""
    
    @classmethod
    @abstractmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Pure computation: TAInput → TAOutput."""
```

### WindowSpec (core/spec.py)

```python
class WindowSpec(BaseModel):
    lookback_bars: int = 0      # Historical bars required
    min_lag_bars: int = 0       # Minimum bars for warm-up
    only_closed: bool = True    # Exclude incomplete candles
```

### RawDataRequirement (core/spec.py)

```python
class RawDataRequirement(BaseModel):
    kind: Literal["price", "oi", "funding", "mark_price"]
    price_field: Optional[Literal["open", "high", "low", "close", "volume"]] = None
    window: WindowSpec = WindowSpec()
    symbols: Optional[Sequence[str]] = None  # None = inherit
    only_closed: bool = True
```

### IndicatorRef (core/spec.py)

```python
class IndicatorRef(BaseModel):
    name: str
    params: Dict[str, Any] = {}
    symbols: Optional[Sequence[str]] = None
    window: WindowSpec = WindowSpec()
```

### TAInput (core/io.py)

```python
class TAInput(BaseModel):
    candles: Mapping[str, Sequence[Candle]]
    oi: Optional[Mapping[str, Sequence[OIPoint]]] = None
    funding: Optional[Mapping[str, Sequence[FundingPoint]]] = None
    mark_price: Optional[Mapping[str, Sequence[MarkPricePoint]]] = None
    indicators: Optional[Mapping[Tuple[str, str, str], Any]] = None  # (name, hash, symbol)
    scope_symbols: Sequence[str]
    eval_ts: Optional[datetime] = None
```

### TAOutput (core/io.py)

```python
class TAOutput(BaseModel):
    name: str
    values: Mapping[str, Any]  # Per-symbol results
    ts: Optional[datetime] = None
    meta: dict[str, Any] = {}
```

---

## Registry (core/registry.py)

```python
INDICATORS: Dict[str, Type[BaseIndicator]] = {}

def register(indicator_cls: Type[BaseIndicator]) -> None:
    """Auto-register indicator by .name."""

def get_indicator(name: str) -> Optional[Type[BaseIndicator]]:
    """Retrieve indicator class."""
```

---

## Planner (core/plan.py)

### Key Types

```python
class ComputeRequest(BaseModel):
    indicator_name: str
    params: Dict[str, Any] = {}
    symbols: Sequence[str]
    eval_ts: Optional[datetime] = None

class ExecutionPlan(BaseModel):
    nodes: List[PlanNode]  # Topologically sorted
```

### Core Functions

```python
def stable_params_hash(params: Dict[str, Any]) -> str:
    """SHA256 hash of canonical JSON params (16 chars)."""

def build_execution_plan(req: ComputeRequest) -> ExecutionPlan:
    """Resolve dependencies → DAG → topological sort → detect cycles."""

def fetch_raw_slices(nodes: List[PlanNode]) -> Dict[Tuple, Any]:
    """Fetch minimal raw data per WindowSpec."""

def execute_plan(plan: ExecutionPlan, raw_cache: Dict) -> TAOutput:
    """Execute DAG: assemble TAInput, call compute(), cache results."""
```

**Algorithm** (build_execution_plan):

1. Get target indicator class from registry
2. DFS to collect dependencies recursively
3. Build adjacency graph: node → [dependencies]
4. Topological sort (Kahn's algorithm)
5. Detect cycles → raise `CyclicDependencyError`
6. Return sorted nodes

---

## Data Models (models/)

### Candle

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
    def hlc3(self) -> Decimal: ...
    
    @property
    def ohlc4(self) -> Decimal: ...
```

### Lightweight Time-Series Points

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
├── trend/            # SMA, EMA, Bollinger
├── momentum/         # RSI, MACD, Stochastic
├── volume/           # VWAP, OBV, MFI
├── volatility/       # ATR
└── cross_asset/      # Correlation
```

### Indicator Template

```python
class ExampleIndicator(BaseIndicator):
    name: ClassVar[str] = "example"
    
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
            
            # Pure math
            closes = [float(c.close) for c in candles[-period:]]
            value = sum(closes) / len(closes)
            results[symbol] = value
        
        return TAOutput(name=cls.name, values=results, ts=input.eval_ts)

# Auto-register
from laakhay.ta.core.registry import register
register(ExampleIndicator)
```

---

## Error Handling

### Indicator Errors

```python
class InsufficientDataError(Exception):
    """Not enough data to compute."""

class InvalidParameterError(Exception):
    """Invalid params."""
```

**Best Practice**: Return empty `values` for insufficient data; raise for invalid params.

### Planner Errors

```python
class IndicatorNotFoundError(Exception):
    """Requested indicator not in registry."""

class CyclicDependencyError(Exception):
    """Dependency graph has cycles."""
```

---

## Testing

### Unit Tests

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

### Integration Tests

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

---

## Performance

### Memory

- **WindowSpec Clipping**: Fetch only `lookback_bars + min_lag_bars`
- **Lazy Evaluation**: Only fetch `scope_symbols`
- **Slice Views**: Avoid copying

### CPU

- **Caching**: Reuse outputs via `(name, params_hash, symbol)` keys
- **Topological Sort**: Compute each node once
- **Pure Python**: Profile first, optimize hotspots later

### Future: Parallelization

- **Per-Symbol**: Execute different symbols in parallel
- **DAG-Level**: Execute independent nodes concurrently
- **Constraint**: Stateless design enables trivial parallelization

---

## Security

- **Input Validation**: Pydantic validators on all models
- **Dependency Audits**: Minimal deps, pin versions, `pip-audit`
- **Data Integrity**: Immutable models (`frozen=True`), deterministic outputs

---

## Glossary

- **Stateless**: No internal state; pure functions
- **Deterministic**: Same input → same output
- **Composable**: Combine/nest via dependency declarations
- **DAG**: Directed Acyclic Graph
- **WindowSpec**: Minimal historical context required
- **params_hash**: SHA-256 hash of canonicalized params
- **eval_ts**: Evaluation timestamp (last closed bar)

---

**End of Architecture**
