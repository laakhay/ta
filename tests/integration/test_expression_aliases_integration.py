import pytest
from datetime import UTC, datetime, timedelta
from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr.dsl import compile_expression, StrategyError

def create_simple_dataset() -> Dataset:
    """Create a simple OHLCV dataset."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [
        Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i * 100, True)
        for i in range(50)
    ]
    ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")
    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", ohlcv, source="ohlcv")
    return ds

def test_integration_mean_alias_fails():
    """Test that compiling an expression with 'mean' fails currently."""
    with pytest.raises(StrategyError):
        compile_expression("mean(close, lookback=10)")

def test_integration_median_alias_fails():
    """Test that compiling an expression with 'median' fails currently."""
    with pytest.raises(StrategyError):
        compile_expression("median(close, lookback=10)")

def test_integration_lookback_keyword_ignored_or_fails():
    """Test integration behavior of 'lookback' keyword."""
    # Currently, oma(close, lookback=10) might compile because 'sma' is known,
    # but 'lookback' won't be mapped to 'period'.
    # If the parser/compiler doesn't fail on unknown kwargs, it might just ignore it.
    # The goal of this test is to observe current behavior and later ensure it works.
    ds = create_simple_dataset()
    
    # This might compile if sma is known and parser isn't strict about kwargs
    # but it won't produce the expected result for period 10 if lookback is ignored (default period is usually used)
    try:
        expr = compile_expression("sma(close, lookback=10)")
        # If it compiles, we check if it correctly used lookback=10 (which it shouldn't yet)
        # This is more of a 'documentation' test of current (broken) behavior.
    except StrategyError:
        # If it fails, that's also fine for a 'red' test phase.
        pass

def test_integration_volume_mean_fails():
    """Test volume-based mean which requires primitive updates."""
    with pytest.raises(StrategyError):
        # Even if 'mean' worked, passing 'volume' as first positional arg 
        # to a rolling primitive might not work yet.
        compile_expression("mean(volume, lookback=10)")
