# Laakhay TA - Implementation Plan

**Version**: 1.0  
**Last Updated**: October 12, 2025

---

## Current Status (30% Complete)

### ✅ Completed
- **Core Contracts**: `BaseIndicator`, `TAInput`, `TAOutput`, `IndicatorRequirements`, `WindowSpec` (100%)
- **Data Models**: `Candle`, `OpenInterest`, `FundingRate`, `MarkPrice` with validators (100%)
- **Registry**: `register()`, `get_indicator()`, `list_indicators()` (100%)
- **Utilities**: `slice_tail()`, `last_closed_ts()`, `ensure_only_closed()`, `zscore()` (100%)
- **Planner Stubs**: `ComputeRequest`, `ExecutionPlan`, `stable_params_hash()` (50%)

### 🚧 In Progress / Blocked
- **Planner Implementation**: DAG resolution, cycle detection, `execute_plan()` (**CRITICAL PATH**)
- **Indicators**: Empty directories, need SMA, EMA, RSI, MACD, VWAP
- **Tests**: No test suite yet
- **CI/CD**: No GitHub Actions

### Priority Roadmap
1. **Week 1**: Testing infrastructure (Phase 1)
2. **Week 2**: Planner implementation (Phase 2) - **BLOCKS EVERYTHING**
3. **Week 3**: Core indicators (Phase 3)
4. **Week 4**: Documentation & polish (Phases 4-6)

---

## Phase 1: Testing Infrastructure

**Goal**: Set up pytest, linting, CI/CD pipeline.

### Commit 1.1: Initialize test structure
```bash
git checkout -b feature/testing-infrastructure
```

**Create**:
```
tests/
├── conftest.py          # pytest fixtures (sample_candles, multi_symbol_candles)
├── unit/
│   ├── core/
│   │   ├── test_registry.py
│   │   ├── test_spec.py
│   │   └── test_utils.py
│   └── models/
│       └── test_candle.py
├── integration/
│   └── test_planner.py
└── property/
    └── test_indicator_properties.py
```

**Key Tests**:
- `test_registry.py`: Register, get, list indicators
- `test_candle.py`: Validators (high >= low, etc.), hlc3/ohlc4 properties
- `conftest.py`: Fixtures for generating test candles

**Commit**: `feat: Initialize test infrastructure with pytest fixtures`

---

### Commit 1.2: Add CI/CD pipeline
**Create**: `.github/workflows/test.yml`

**Jobs**:
- Lint with Ruff
- Format check with Black
- Type check with mypy
- Run pytest with coverage (Python 3.10-3.13)

**Commit**: `ci: Add GitHub Actions workflow for testing`

---

### Commit 1.3: Add unit tests for core modules
**Tests**:
- `test_spec.py`: WindowSpec defaults, RawDataRequirement validation
- `test_utils.py`: `slice_tail()`, `zscore()` correctness
- `test_io.py`: TAInput/TAOutput immutability

**Commit**: `test: Add unit tests for core contracts and utilities`

---

## Phase 2: Planner Implementation (**CRITICAL PATH**)

**Goal**: Implement full DAG resolution, cycle detection, execution orchestration.

### Commit 2.1: Implement `build_execution_plan` (DAG resolution)
**Edit**: `laakhay/ta/core/plan.py`

**Algorithm**:
```python
def build_execution_plan(req: ComputeRequest) -> ExecutionPlan:
    # 1. Get target indicator class
    target_cls = get_indicator(req.indicator_name)
    if not target_cls:
        raise IndicatorNotFoundError(req.indicator_name)
    
    # 2. Build dependency graph (DFS)
    graph = {}  # node_key -> [dep_keys]
    visited = set()
    
    def visit(ind_name, params, symbols):
        ind_cls = get_indicator(ind_name)
        reqs = ind_cls.requirements()
        
        # Add raw deps
        for raw_dep in reqs.raw:
            for sym in (raw_dep.symbols or symbols):
                raw_key = ("raw", raw_dep.kind, raw_dep.price_field or "", sym)
                graph.setdefault(raw_key, [])
        
        # Add indicator deps (recursive)
        for ind_dep in reqs.indicators:
            dep_hash = stable_params_hash(ind_dep.params)
            for sym in (ind_dep.symbols or symbols):
                dep_key = ("indicator", ind_dep.name, dep_hash, sym)
                if dep_key not in visited:
                    visited.add(dep_key)
                    visit(ind_dep.name, ind_dep.params, [sym])
                graph.setdefault((ind_name, params_hash, sym), []).append(dep_key)
    
    visit(req.indicator_name, req.params, req.symbols)
    
    # 3. Topological sort (Kahn's algorithm)
    in_degree = {node: 0 for node in graph}
    for deps in graph.values():
        for dep in deps:
            in_degree[dep] = in_degree.get(dep, 0) + 1
    
    queue = [node for node in graph if in_degree[node] == 0]
    sorted_nodes = []
    
    while queue:
        node = queue.pop(0)
        sorted_nodes.append(node)
        for dep in graph.get(node, []):
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)
    
    if len(sorted_nodes) != len(graph):
        raise CyclicDependencyError("Dependency cycle detected")
    
    return ExecutionPlan(nodes=[PlanNode.from_key(k) for k in sorted_nodes])
```

**Tests**: `test_planner.py` - simple deps, nested deps, cycle detection

**Commit**: `feat(planner): Implement DAG resolution with cycle detection`

---

### Commit 2.2: Implement `fetch_raw_slices` adapter interface
**Edit**: `laakhay/ta/core/plan.py`

**Interface**:
```python
from abc import ABC, abstractmethod

class DataAdapter(ABC):
    """Abstract interface for data sources."""
    
    @abstractmethod
    def fetch_candles(self, symbol: str, window: WindowSpec, eval_ts: datetime) -> Sequence[Candle]:
        """Fetch candle history for symbol."""
    
    @abstractmethod
    def fetch_oi(self, symbol: str, window: WindowSpec, eval_ts: datetime) -> Sequence[OIPoint]:
        """Fetch open interest history."""

def fetch_raw_slices(
    nodes: List[PlanNode],
    adapter: DataAdapter,
    eval_ts: Optional[datetime] = None
) -> Dict[Tuple, Any]:
    """Fetch minimal raw data for all 'raw' nodes."""
    cache = {}
    for node in nodes:
        if node.kind == "raw":
            data_kind, field, symbol = node.key[1], node.key[2], node.key[3]
            if data_kind == "price":
                cache[node.key] = adapter.fetch_candles(symbol, node.window, eval_ts)
            elif data_kind == "oi":
                cache[node.key] = adapter.fetch_oi(symbol, node.window, eval_ts)
    return cache
```

**Tests**: Mock adapter, verify WindowSpec clipping

**Commit**: `feat(planner): Add DataAdapter interface for fetch_raw_slices`

---

### Commit 2.3: Implement `execute_plan` orchestration
**Edit**: `laakhay/ta/core/plan.py`

**Implementation**:
```python
def execute_plan(
    plan: ExecutionPlan,
    raw_cache: Dict[Tuple, Any],
    request: ComputeRequest
) -> TAOutput:
    """Execute DAG: assemble TAInput, call compute(), cache results."""
    indicator_cache = {}
    target_output = None
    
    for node in plan.nodes:
        if node.kind == "raw":
            continue  # Already in raw_cache
        
        # Assemble TAInput
        ind_name, params_hash, symbol = node.key[1], node.key[2], node.key[3]
        ind_cls = get_indicator(ind_name)
        
        candles = {}
        for sym in request.symbols:
            raw_key = ("raw", "price", "close", sym)  # Simplified
            candles[sym] = raw_cache.get(raw_key, [])
        
        # Inject upstream deps
        injected = {}
        for dep_ref in ind_cls.requirements().indicators:
            dep_hash = stable_params_hash(dep_ref.params)
            for sym in request.symbols:
                dep_key = (dep_ref.name, dep_hash, sym)
                if dep_key in indicator_cache:
                    injected[dep_key] = indicator_cache[dep_key]
        
        ta_input = TAInput(
            candles=candles,
            indicators=injected or None,
            scope_symbols=request.symbols,
            eval_ts=request.eval_ts
        )
        
        # Compute
        output = ind_cls.compute(ta_input, **node.params)
        
        # Cache per-symbol
        for sym, val in output.values.items():
            cache_key = (ind_name, params_hash, sym)
            indicator_cache[cache_key] = val
        
        # Save if target
        if ind_name == request.indicator_name:
            target_output = output
    
    return target_output
```

**Tests**: End-to-end with dummy indicators

**Commit**: `feat(planner): Implement execute_plan orchestration`

---

## Phase 3: Core Indicators

**Goal**: Implement 5 essential indicators with full tests.

### Commit 3.1: Implement SMA (Simple Moving Average)
**Create**: `laakhay/ta/indicators/trend/sma.py`

```python
class SMAIndicator(BaseIndicator):
    name: ClassVar[str] = "sma"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field="close",
                    window=WindowSpec(lookback_bars=200),  # Max reasonable period
                    only_closed=True
                )
            ]
        )
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        period = params.get("period", 20)
        results = {}
        
        for symbol in input.scope_symbols:
            candles = input.candles.get(symbol, [])
            if len(candles) < period:
                continue
            
            closes = [float(c.close) for c in candles[-period:]]
            sma = sum(closes) / len(closes)
            results[symbol] = sma
        
        return TAOutput(name=cls.name, values=results, ts=input.eval_ts)
```

**Tests**: Correctness, insufficient data, determinism, property-based

**Commit**: `feat(indicators): Implement SMA with tests`

---

### Commit 3.2: Implement EMA (Exponential Moving Average)
**Create**: `laakhay/ta/indicators/trend/ema.py`

**Algorithm**: Standard EMA with smoothing factor `α = 2 / (period + 1)`

**Tests**: Compare against known values, test smoothing property

**Commit**: `feat(indicators): Implement EMA with tests`

---

### Commit 3.3: Implement RSI (Relative Strength Index)
**Create**: `laakhay/ta/indicators/momentum/rsi.py`

**Algorithm**: Wilder's smoothing for gains/losses

**Tests**: Known values (overbought/oversold), range [0, 100]

**Commit**: `feat(indicators): Implement RSI with tests`

---

### Commit 3.4: Implement MACD (depends on EMA)
**Create**: `laakhay/ta/indicators/momentum/macd.py`

```python
class MACDIndicator(BaseIndicator):
    name: ClassVar[str] = "macd"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(
            indicators=[
                IndicatorRef(name="ema", params={"period": 12}),
                IndicatorRef(name="ema", params={"period": 26}),
            ]
        )
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        signal_period = params.get("signal", 9)
        results = {}
        
        for symbol in input.scope_symbols:
            ema12_key = ("ema", stable_params_hash({"period": 12}), symbol)
            ema26_key = ("ema", stable_params_hash({"period": 26}), symbol)
            
            ema12 = input.indicators.get(ema12_key)
            ema26 = input.indicators.get(ema26_key)
            
            if ema12 is None or ema26 is None:
                continue
            
            macd_line = ema12 - ema26
            # ... compute signal line (EMA of MACD line)
            results[symbol] = {"macd": macd_line, "signal": signal, "histogram": hist}
        
        return TAOutput(name=cls.name, values=results, ts=input.eval_ts)
```

**Tests**: Dependency injection, correct calculation

**Commit**: `feat(indicators): Implement MACD with EMA dependencies`

---

### Commit 3.5: Implement VWAP (Volume Weighted Average Price)
**Create**: `laakhay/ta/indicators/volume/vwap.py`

**Requirements**: Both `price` (close) and `volume`

**Tests**: Volume weighting correctness

**Commit**: `feat(indicators): Implement VWAP with volume dependency`

---

## Phase 4: Cross-Asset & Advanced Features

### Commit 4.1: Implement Correlation indicator (multi-symbol)
**Create**: `laakhay/ta/indicators/cross_asset/correlation.py`

**Tests**: Pearson correlation, multi-symbol TAInput

**Commit**: `feat(indicators): Implement cross-asset correlation`

---

### Commit 4.2: Add spike detection signal
**Create**: `laakhay/ta/signals/spike_detection.py`

**Algorithm**: Z-score based spike detection

**Commit**: `feat(signals): Implement spike detection`

---

## Phase 5: Documentation & Examples

### Commit 5.1: Update README with quickstart
**Edit**: `README.md`

**Add**: Installation, basic example, API reference link

**Commit**: `docs: Update README with quickstart guide`

---

### Commit 5.2: Add end-to-end examples
**Create**: `examples/quickstart.py`, `examples/multi_symbol.py`

**Commit**: `docs: Add end-to-end usage examples`

---

## Phase 6: Production Readiness

### Commit 6.1: Add performance benchmarks
**Create**: `benchmarks/benchmark_indicators.py`

**Commit**: `perf: Add benchmark suite for indicators`

---

### Commit 6.2: Optimize hotspots (if needed)
**Profile**: Identify bottlenecks in planner or indicators

**Commit**: `perf: Optimize <specific_hotspot>`

---

### Commit 6.3: Final polish & release prep
- Version bump to `0.1.0`
- Changelog generation
- PyPI metadata

**Commit**: `chore: Prepare v0.1.0 release`

---

## Summary

**Total Estimated Work**: 30-35 commits across 6 phases  
**Critical Path**: Phase 2 (Planner) blocks Phase 3+ (Indicators)  
**Completion Timeline**: 4-6 weeks with focused effort

**Next Action**: Start Phase 1 (Testing Infrastructure) → `git checkout -b feature/testing-infrastructure`
