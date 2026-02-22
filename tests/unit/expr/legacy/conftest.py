"""Pytest configuration for legacy compatibility tests."""

import pytest

from laakhay.ta.core.dataset import Dataset


@pytest.fixture
def sample_dataset(sample_ohlcv_data):
    """Dataset built from sample OHLCV for expression evaluation."""
    from laakhay.ta.core.ohlcv import OHLCV

    ohlcv = OHLCV(
        timestamps=sample_ohlcv_data["timestamps"],
        opens=sample_ohlcv_data["opens"],
        highs=sample_ohlcv_data["highs"],
        lows=sample_ohlcv_data["lows"],
        closes=sample_ohlcv_data["closes"],
        volumes=sample_ohlcv_data["volumes"],
        is_closed=sample_ohlcv_data["is_closed"],
        symbol=sample_ohlcv_data["symbol"],
        timeframe=sample_ohlcv_data["timeframe"],
    )
    dataset = Dataset()
    dataset.add_series(ohlcv.symbol, ohlcv.timeframe, ohlcv, "ohlcv")
    return dataset
