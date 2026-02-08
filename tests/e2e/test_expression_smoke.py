
import pytest
from datetime import datetime, timedelta, timezone
from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr.dsl import compile_expression

def create_dataset() -> Dataset:
    """Create a simple OHLCV dataset with predictable values."""
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bars = []
    # Create 50 bars
    # Close = 100, 101, 102...
    # Volume = 1000, 1100, 1200...
    for i in range(50):
        bars.append(Bar.from_raw(
            ts=base + timedelta(hours=i),
            open=100.0 + i,
            high=105.0 + i,
            low=95.0 + i,
            close=100.0 + i,
            volume=1000.0 + (i * 100),
            is_closed=True
        ))
    
    ohlcv = OHLCV.from_bars(bars, symbol="BTC/USDT", timeframe="1h")
    ds = Dataset()
    ds.add_series("BTC/USDT", "1h", ohlcv, source="ohlcv")
    return ds

def test_end_to_end_alias_execution():
    """Test full execution of expression with aliases."""
    ds = create_dataset()
    
    # 1. Parse & Compile "mean(volume, lookback=10)"
    # Uses:
    # - 'mean' alias for 'rolling_mean'
    # - 'volume' field shorthand (positional arg converted to field='volume')
    # - 'lookback' alias for 'period' parameter
    expr_text = "mean(volume, lookback=10)"
    pipeline = compile_expression(expr_text)
    
    assert pipeline is not None, "Pipeline compilation failed"
    
    # 2. Execute
    # The pipeline should handle planning internally
    results = pipeline.run(ds)
    
    # 3. Verify
    # Expect output for BTC/USDT 1h
    key = ("BTC/USDT", "1h", "default")
    assert key in results, f"Result key {key} not found in {list(results.keys())}"
    
    series = results[key]
    
    # Check length
    # The pipeline returns series aligned to valid data. 
    # rolling_mean(10) requires 10 bars. 50 - 10 + 1 = 41 bars.
    assert len(series) == 41
    
    # Check values
    # rolling_mean of volume with period 10
    # verify last value
    # last 10 volumes: 4000, 4100 ... 4900 (for i=49)
    # i=40 to 49
    # volumes: 1000 + i*100
    # sum = sum(1000 + i*100 for i in range(40, 50))
    #     = 1000*10 + 100 * sum(40..49)
    #     = 10000 + 100 * (40+49)*10/2 = 10000 + 100 * 445 = 10000 + 44500 = 54500
    # mean = 54500 / 10 = 5450.0
    
    last_val = series.values[-1]
    assert last_val == 5450.0
    
    # Check availability mask 
    # Since the series is already sliced to valid data, mostly valid
    assert series.availability_mask[-1]
    # The first element might be False depending on exact alignment logic, 
    # but the end of the series must be valid.

def test_end_to_end_median_implicit_close():
    """Test median alias with implicit close."""
    ds = create_dataset()
    
    # "median(20)" -> rolling_median(close, period=20)
    pipeline = compile_expression("median(20)")
    results = pipeline.run(ds)
    
    series = results[("BTC/USDT", "1h", "default")]
    # rolling_median(20) requires 20 bars. 50 - 20 + 1 = 31 bars.
    assert len(series) == 31
    
    # rolling_median implementation uses sorted(w)[len(w) // 2]
    # For even n=20, index 10 is used (upper median).
    # 20 items: 0..19. Index 10 is the 11th item.
    # Dataset values are 130..149.
    # Median is 140.
    assert series.values[-1] == 140.0
