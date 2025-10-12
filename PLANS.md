# Laakhay TA - Implementation Plan

**Version**: 2.0  
**Status**: v0.1.0 Foundation Complete  
**Last Updated**: October 12, 2025

---

## Current Status (v0.1.0 - 80% Complete)

### ✅ Phase 1-3: Foundation Complete
- **Core Infrastructure** (100%): BaseIndicator, Registry, DAG Planner, Execution Engine
- **Data Models** (100%): Candle, OpenInterest, FundingRate, MarkPrice
- **Testing Infrastructure** (100%): 30 tests, 79% coverage, pytest + fixtures
- **Tier 1 Indicators** (80%): SMA, EMA, RSI, MACD, Stochastic, ATR, BBands, VWAP

### 🎯 Immediate Priorities

#### Phase 4: Production Readiness (Next 2 weeks)
1. **PyPI Packaging** - Make installable via `pip install laakhay-ta`
2. **Integration Layer** - Connect with laakhay-data for real-time/historical data
3. **Performance Testing** - Benchmark indicator computation speed
4. **CI/CD** - GitHub Actions for automated testing

#### Phase 5: Tier 2 Indicators (Weeks 3-4)
- **Trend**: Ichimoku Cloud, Parabolic SAR, Supertrend
- **Momentum**: ADX (Directional Movement), CCI
- **Volume**: OBV (On-Balance Volume), MFI (Money Flow Index)

#### Phase 6: Advanced Features (Month 2)
- **Streaming Indicators**: Real-time updates (not full recalculation)
- **Multi-Timeframe**: Compute indicators across multiple timeframes
- **Cross-Asset**: Correlation, spread analysis
- **Signal Generation**: Crossover detection, divergence detection
- **Plan Optimization**: Cache reuse, parallel execution

---

## Detailed Roadmap

### Phase 4: Production Ready (v0.2.0)

**Week 1: Packaging & Integration**
```bash
# Commit 4.1: PyPI packaging
- Update pyproject.toml with metadata
- Test installation: pip install -e .
- Publish to Test PyPI
- Commit: "chore: Prepare PyPI packaging for v0.2.0"

# Commit 4.2: laakhay-data integration
- Create adapter: LaakhayDataAdapter(DataAdapter)
- Implement fetch_candles() using laakhay.data.DataFeed
- Add integration tests with real Binance data
- Commit: "feat: Add laakhay-data integration adapter"

# Commit 4.3: Example implementations
- examples/quickstart.py (basic RSI)
- examples/strategy.py (multi-indicator strategy)
- examples/backtest.py (simple backtest loop)
- Commit: "docs: Add real-world usage examples"
```

**Week 2: CI/CD & Benchmarks**
```bash
# Commit 4.4: GitHub Actions
- .github/workflows/test.yml (pytest, coverage, lint)
- .github/workflows/publish.yml (PyPI auto-publish on tag)
- Commit: "ci: Add GitHub Actions for testing and publishing"

# Commit 4.5: Performance benchmarks
- benchmarks/indicators.py (time 10k candles for each indicator)
- Document performance characteristics
- Commit: "perf: Add performance benchmarks and baseline"
```

---

### Phase 5: Tier 2 Indicators (v0.3.0)

**Week 3: Advanced Trend & Momentum**
```bash
# ADX (Average Directional Index)
laakhay/ta/indicators/momentum/adx.py
- Requirements: High, Low, Close + 14 period smoothing
- Returns: {"adx": value, "plus_di": value, "minus_di": value}
- Commit: "feat(indicators): Add ADX with directional indicators"

# Ichimoku Cloud
laakhay/ta/indicators/trend/ichimoku.py
- Requirements: 52-period lookback
- Returns: {"tenkan": ..., "kijun": ..., "senkou_a": ..., "senkou_b": ..., "chikou": ...}
- Commit: "feat(indicators): Add Ichimoku Cloud"

# Parabolic SAR
laakhay/ta/indicators/trend/psar.py
- Requirements: High, Low, acceleration factor
- Returns: Series of stop/reverse levels
- Commit: "feat(indicators): Add Parabolic SAR"
```

**Week 4: Volume & Additional**
```bash
# OBV (On-Balance Volume)
laakhay/ta/indicators/volume/obv.py
- Requirements: Close, Volume
- Returns: Cumulative volume-direction series
- Commit: "feat(indicators): Add OBV"

# MFI (Money Flow Index)
laakhay/ta/indicators/volume/mfi.py
- Requirements: High, Low, Close, Volume
- Returns: 0-100 oscillator (volume-weighted RSI)
- Commit: "feat(indicators): Add MFI"
```

---

### Phase 6: Advanced Features (v0.4.0)

**Streaming Architecture**
```python
# New: StreamIndicator base class
class StreamIndicator(BaseIndicator):
    kind: ClassVar[Literal["stream"]] = "stream"
    
    @classmethod
    @abstractmethod
    def init_state(cls, **params) -> Any:
        """Initialize stateful computation."""
    
    @classmethod
    @abstractmethod
    def update(cls, state: Any, new_candle: Candle, **params) -> Tuple[Any, float]:
        """Update state with new candle, return (new_state, indicator_value)."""

# Example: StreamEMA
class StreamEMA(StreamIndicator):
    name: ClassVar[str] = "stream_ema"
    
    @classmethod
    def init_state(cls, initial_candles: List[Candle], period: int) -> float:
        """Return initial EMA from first `period` candles."""
        closes = [float(c.close) for c in initial_candles[:period]]
        return sum(closes) / len(closes)
    
    @classmethod
    def update(cls, state: float, new_candle: Candle, period: int) -> Tuple[float, float]:
        """Update EMA with new close."""
        alpha = 2 / (period + 1)
        new_ema = alpha * float(new_candle.close) + (1 - alpha) * state
        return new_ema, new_ema
```

**Multi-Timeframe**
```python
# New: compute request with timeframe parameter
req = ComputeRequest(
    indicator_name="rsi",
    params={"period": 14},
    symbols=["BTCUSDT"],
    eval_ts=datetime.now(),
    timeframe="1h",  # NEW: aggregate raw 1m data to 1h bars
)
```

**Cross-Asset Analysis**
```python
# New: Correlation indicator
class CorrelationIndicator(BaseIndicator):
    name: ClassVar[str] = "correlation"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        return IndicatorRequirements(
            raw=[RawDataRequirement(kind="price", price_field="close")]
        )
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Compute pairwise correlation between all symbols in scope."""
        period = params.get("period", 20)
        
        # Build price matrix
        price_matrix = {}
        for sym in input.scope_symbols:
            candles = input.candles.get(sym, [])[-period:]
            price_matrix[sym] = [float(c.close) for c in candles]
        
        # Compute Pearson correlation
        correlations = {}
        for sym1 in input.scope_symbols:
            for sym2 in input.scope_symbols:
                if sym1 < sym2:  # Avoid duplicates
                    corr = pearson(price_matrix[sym1], price_matrix[sym2])
                    correlations[f"{sym1}_{sym2}"] = corr
        
        return TAOutput(name=cls.name, values=correlations)
```

---

## Testing Strategy

### Coverage Goals
- **Core Modules**: 90%+ (plan.py, registry.py, spec.py)
- **Indicators**: 80%+ (each indicator thoroughly tested)
- **Integration**: Key workflows end-to-end

### Test Categories
```
tests/
├── unit/                    # Fast, isolated (< 1s total)
│   ├── core/
│   ├── indicators/
│   └── models/
├── integration/             # Real data adapters (< 10s total)
│   ├── test_laakhay_data_integration.py
│   └── test_execution_plan_e2e.py
└── benchmarks/              # Performance tests (run manually)
    └── benchmark_indicators.py
```

---

## Release Schedule

| Version | Status | Features | Target Date |
|---------|--------|----------|-------------|
| v0.1.0 | ✅ Complete | Core + 8 indicators + Tests | Oct 12, 2025 |
| v0.2.0 | 🚧 Next | PyPI + Integration + CI/CD | Oct 26, 2025 |
| v0.3.0 | 📋 Planned | Tier 2 indicators (5+) | Nov 9, 2025 |
| v0.4.0 | 💡 Future | Streaming + Multi-TF + Cross-Asset | Dec 2025 |

---

## Success Metrics

**v0.1.0** ✅
- [x] 8 production-ready indicators
- [x] 30 passing tests (79% coverage)
- [x] Full documentation
- [x] Stateless, deterministic architecture

**v0.2.0** (Next)
- [ ] PyPI installable
- [ ] Real-time data integration
- [ ] CI/CD automated
- [ ] Performance benchmarked (< 1ms per indicator per symbol)

**v0.3.0**
- [ ] 15+ total indicators
- [ ] 90%+ test coverage
- [ ] Production usage by 3+ projects

**v1.0.0** (Q1 2026)
- [ ] Streaming indicators
- [ ] Multi-timeframe support
- [ ] 25+ indicators
- [ ] 95%+ coverage
- [ ] Production-proven at scale

---

## Next Actions

1. **Immediate**: Create PyPI release for v0.2.0
2. **This Week**: Implement LaakhayDataAdapter
3. **Next Week**: Set up GitHub Actions CI/CD
4. **Month**: Add 5 Tier 2 indicators

**Current Branch**: `main` (v0.1.0 foundation complete)  
**Next Branch**: `feature/pypi-packaging` → v0.2.0

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
