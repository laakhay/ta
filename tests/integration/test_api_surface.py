from datetime import datetime, timedelta

import pytest

from laakhay.ta import Price, Series, ta


@pytest.fixture
def sample_series():
    return Series[Price](
        timestamps=tuple(datetime(2023, 1, 1) + timedelta(minutes=i) for i in range(100)),
        values=tuple(Price(100 + i) for i in range(100)),
        symbol="BTCUSDT",
        timeframe="1m",
    )


def test_categorical_access(sample_series):
    # Test Trend
    assert hasattr(ta, "trend")
    assert hasattr(ta.trend, "sma")
    res = ta.trend.sma(sample_series, period=20)
    assert isinstance(res, Series)

    # Test Momentum
    assert hasattr(ta, "momentum")
    assert hasattr(ta.momentum, "rsi")
    res = ta.momentum.rsi(sample_series, period=14)
    assert isinstance(res, Series)

    # Test Volatility
    assert hasattr(ta, "volatility")
    assert hasattr(ta.volatility, "bbands")
    res = ta.volatility.bbands(sample_series, period=20)
    # BBands returns a handle or expression depending on args,
    # but here it should work if called correctly via manual wrapper
    assert res is not None

    # Test Volume
    assert hasattr(ta, "volume")
    assert hasattr(ta.volume, "obv")
    # OBV needs volume, so let's mock a context if needed, but ta.obv(series) should work if series has volume in context

    # Test Primitives
    assert hasattr(ta, "primitives")
    assert hasattr(ta.primitives, "rolling_mean")
    res = ta.primitives.rolling_mean(sample_series, period=10)
    assert isinstance(res, Series)


def test_top_level_backwards_compatibility(sample_series):
    # Verify sma is still available at top level ta
    assert hasattr(ta, "sma")
    res = ta.sma(sample_series, period=20)
    assert isinstance(res, Series)

    # Verify new indicators are also at top level
    assert hasattr(ta, "adx")
    assert hasattr(ta, "supertrend")
    assert hasattr(ta, "keltner")
    assert hasattr(ta, "cmf")
