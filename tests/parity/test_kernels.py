import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.primitives.kernel import run_kernel
from laakhay.ta.primitives.kernels.ema import EMAKernel
from laakhay.ta.primitives.kernels.rolling import RollingMeanKernel, RollingStdKernel, RollingSumKernel


@pytest.fixture
def mock_series() -> Series[Price]:
    timestamps = tuple(f"2023-01-{i:02d}" for i in range(1, 21))
    # Values: 1, 2, 3, 4, 5... 20
    values = tuple(Price(str(i)) for i in range(1, 21))
    return Series[Price](timestamps=timestamps, values=values, symbol="TEST", timeframe="1d")


def test_rolling_sum_kernel(mock_series: Series[Price]):
    kernel = RollingSumKernel()
    res = run_kernel(mock_series, kernel, min_periods=3, period=3)

    assert len(res) == 18  # 20 - 3 + 1
    # First valid sum over (1,2,3) = 6
    assert res.values[0] == Price("6")
    # Second valid sum over (2,3,4) = 9
    assert res.values[1] == Price("9")


def test_rolling_mean_kernel(mock_series: Series[Price]):
    kernel = RollingMeanKernel()
    res = run_kernel(mock_series, kernel, min_periods=3, period=3)

    assert len(res) == 18
    # Mean of (1,2,3) = 2
    assert res.values[0] == Price("2")
    # Mean of (2,3,4) = 3
    assert res.values[1] == Price("3")


def test_rolling_std_kernel():
    # specifically test std dev
    timestamps = tuple(f"2023-01-{i:02d}" for i in range(1, 5))
    # Using 2, 4, 4, 4, 5, 5, 7, 9 -> let's do 2, 4, 4, 6
    values = tuple(Price(str(v)) for v in [2, 4, 4, 6])
    s = Series[Price](timestamps=timestamps, values=values, symbol="TEST", timeframe="1d")

    kernel = RollingStdKernel()
    res = run_kernel(s, kernel, min_periods=4, period=4)

    assert len(res) == 1
    # mean of [2, 4, 4, 6] = 4
    # var = ((2-4)^2 + (4-4)^2 + (4-4)^2 + (6-4)^2) / 4
    # var = (4 + 0 + 0 + 4) / 4 = 2
    # std = sqrt(2) ~= 1.4142...

    std_val = float(str(res.values[0]))
    assert abs(std_val - 1.4142135623730951) < 1e-6


def test_ema_kernel(mock_series: Series[Price]):
    kernel = EMAKernel()
    # period=3 => alpha = 2/(3+1) = 0.5
    res = run_kernel(mock_series, kernel, min_periods=1, period=3)

    assert len(res) == 20
    # First EMA is just the first value
    assert res.values[0] == Price("1")

    # Second EMA = 0.5 * 2 + 0.5 * 1 = 1.5
    assert res.values[1] == Price("1.5")

    # Third EMA = 0.5 * 3 + 0.5 * 1.5 = 1.5 + 0.75 = 2.25
    assert res.values[2] == Price("2.25")
