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


def test_strict_categorical_access(sample_series):
    # Verify sma is NO LONGER available at top level ta
    with pytest.raises(AttributeError, match="no longer available at the top-level"):
        ta.sma(sample_series, period=20)

    # Verify others also gone
    with pytest.raises(AttributeError):
        ta.adx(sample_series)
    with pytest.raises(AttributeError):
        ta.supertrend(sample_series)
    with pytest.raises(AttributeError):
        ta.bbands(sample_series)
    with pytest.raises(AttributeError):
        ta.obv(sample_series)
