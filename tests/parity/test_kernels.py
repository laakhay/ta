import pytest

import ta_py
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price


@pytest.fixture
def mock_series() -> Series[Price]:
    timestamps = tuple(f"2023-01-{i:02d}" for i in range(1, 21))
    # Values: 1, 2, 3, 4, 5... 20
    values = tuple(Price(str(i)) for i in range(1, 21))
    return Series[Price](timestamps=timestamps, values=values, symbol="TEST", timeframe="1d")


def test_rolling_sum_kernel(mock_series: Series[Price]):
    res = ta_py.rolling_sum([float(v) for v in mock_series.values], 3)

    assert len(res) == 20  # Full length
    # First valid sum over (1,2,3) = 6 at index 2
    assert res[2] == 6.0
    # Second valid sum over (2,3,4) = 9 at index 3
    assert res[3] == 9.0


def test_rolling_mean_kernel(mock_series: Series[Price]):
    res = ta_py.rolling_mean([float(v) for v in mock_series.values], 3)

    assert len(res) == 20  # Full length
    # Mean of (1,2,3) = 2 at index 2
    assert res[2] == 2.0
    # Mean of (2,3,4) = 3 at index 3
    assert res[3] == 3.0


def test_rolling_std_kernel():
    # specifically test std dev
    timestamps = tuple(f"2023-01-{i:02d}" for i in range(1, 5))
    # Using 2, 4, 4, 4, 5, 5, 7, 9 -> let's do 2, 4, 4, 6
    values = tuple(Price(str(v)) for v in [2, 4, 4, 6])
    res = ta_py.rolling_std([float(v) for v in values], 4)
    assert len(res) == 4
    # mean of [2, 4, 4, 6] = 4
    # var = ((2-4)^2 + (4-4)^2 + (4-4)^2 + (6-4)^2) / 4
    # var = (4 + 0 + 0 + 4) / 4 = 2
    # std = sqrt(2) ~= 1.4142...

    std_val = float(res[3])  # 4th value is first valid for min_periods=4
    assert abs(std_val - 1.4142135623730951) < 1e-6


def test_ema_kernel(mock_series: Series[Price]):
    # period=3 => alpha = 2/(3+1) = 0.5
    res = ta_py.rolling_ema([float(v) for v in mock_series.values], 3)

    assert len(res) == 20
    # First EMA is just the first value
    assert res[0] == 1.0

    # Second EMA = 0.5 * 2 + 0.5 * 1 = 1.5
    assert res[1] == 1.5

    # Third EMA = 0.5 * 3 + 0.5 * 1.5 = 1.5 + 0.75 = 2.25
    assert res[2] == 2.25


def test_rust_rolling_sum_smoke():
    out = ta_py.rolling_sum([1.0, 2.0, 3.0, 4.0], 3)
    assert out[2] == 6.0
    assert out[3] == 9.0
