# Laakhay TA - Roadmap

**Version**: 1.0 | **Status**: v0.1.0 Complete (80%) | **Updated**: Oct 12, 2025

---

## Current Status

**v0.1.0 Foundation Complete**

- Core: BaseIndicator, Registry, DAG Planner, Execution Engine ✅
- Data Models: Candle, OI, Funding, MarkPrice ✅
- Indicators: SMA, EMA, RSI, MACD, Stochastic, ATR, BBands, VWAP ✅
- Analytics: Correlation, Relative Strength, Volume, Statistics ✅
- Testing: 98 tests, 79% core + 92-100% analytics ✅
- Spike Detection: Abstracted from crypto-alerts-backend ✅

---

## Roadmap

### v0.2.0 - Production Ready (2 weeks)

**Week 1: Packaging & Integration**

- PyPI packaging (`pip install laakhay-ta`)
- laakhay-data integration (LaakhayDataAdapter)
- Usage examples (quickstart, strategy, backtest)

**Week 2: CI/CD & Benchmarks**

- GitHub Actions (test, lint, publish)
- Performance benchmarks (< 1ms/indicator/symbol)

### v0.3.0 - Tier 2 Indicators (2 weeks)

**Week 3: Advanced Indicators**

- ADX (Average Directional Index)
- Ichimoku Cloud
- Parabolic SAR

**Week 4: Volume Indicators**

- OBV (On-Balance Volume)
- MFI (Money Flow Index)

### v0.4.0 - Advanced Features (4 weeks)

**Streaming Architecture**

```python
class StreamIndicator(BaseIndicator):
    kind: ClassVar[Literal["stream"]] = "stream"
  
    @classmethod
    def init_state(cls, **params) -> Any:
        """Initialize stateful computation."""
  
    @classmethod
    def update(cls, state: Any, new_candle: Candle, **params) -> Tuple[Any, float]:
        """Update state with new candle."""
```

**Multi-Timeframe Support**

```python
req = ComputeRequest(
    indicator_name="rsi",
    params={"period": 14},
    symbols=["BTCUSDT"],
    timeframe="1h"  # Aggregate raw 1m to 1h
)
```

**Signal Generation**

- Crossover detection
- Divergence detection
- Custom signal composition

---

## Backend Migration Status

**Extracted from crypto-alerts-backend** (5 modules):

1. **Spike Detection** ✅
   - PriceSpikeDetector, VolumeSpikeDetector, CombinedSpikeDetector
   - 13 tests, 81% coverage
   - Location: `laakhay/ta/signals/spikes.py`

2. **Correlation Analysis** ✅
   - CorrelationAnalyzer with Pearson correlation
   - Rolling correlation, correlation change detection
   - 14 tests, 92% coverage
   - Location: `laakhay/ta/analytics/correlation.py`

3. **Relative Strength** ✅
   - RelativeStrengthAnalyzer for performance vs base asset
   - Divergence detection, ranking
   - 13 tests, 97% coverage
   - Location: `laakhay/ta/analytics/relative_strength.py`

4. **Volume Analysis** ✅
   - VolumeAnalyzer with multi-window baseline comparison
   - Percentile ranking, z-score calculation
   - 16 tests, 100% coverage
   - Location: `laakhay/ta/analytics/volume.py`

5. **Statistical Utilities** ✅
   - Returns (log/pct/simple), volatility, Sharpe ratio
   - Percentile rank, z-score
   - 25 tests, 100% coverage
   - Location: `laakhay/ta/analytics/statistics.py`

**Total**: 81 tests for backend features, 68 tests for analytics (92-100% coverage)

**Next Steps**:
- Integrate into crypto-alerts-backend
- Remove legacy implementations
- Performance benchmarks (target: <1ms per calculation)

---

## Release Schedule

| Version | Features                    | Target    |
| ------- | --------------------------- | --------- |
| v0.1.0  | Core + 8 indicators + Tests | Oct 12 ✅ |
| v0.1.5  | Analytics + Backend Extract | Oct 13 ✅ |
| v0.2.0  | PyPI + Integration + CI/CD  | Oct 26    |
| v0.3.0  | Tier 2 indicators (5+)      | Nov 9     |
| v0.4.0  | Streaming + Multi-TF        | Dec 2025  |
| v1.0.0  | Production-proven, 25+ ind  | Q1 2026   |

---

## Success Metrics

**v0.2.0**

- PyPI installable
- Real-time data integration
- CI/CD automated
- < 1ms per indicator per symbol

**v0.3.0**

- 15+ total indicators
- 90%+ test coverage
- Production usage by 3+ projects

**v1.0.0**

- Streaming indicators
- Multi-timeframe support
- 25+ indicators
- 95%+ coverage
- Production-proven at scale

---

## Next Actions

1. Create PyPI release (v0.2.0)
2. Implement LaakhayDataAdapter
3. Set up GitHub Actions CI/CD
4. Add 5 Tier 2 indicators

**Current Branch**: `main`
**Next Branch**: `feature/pypi-packaging` → v0.2.0
