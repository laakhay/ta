import pytest

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.expr.runtime.backends.batch import BatchBackend

from .utils import assert_dict_parity, assert_series_parity


@pytest.fixture
def sample_dataset(sample_ohlcv_data) -> Dataset:
    """Fixture providing a sample generic dataset."""
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


@pytest.mark.parametrize(
    "expr_text",
    [
        "sma(close, 14)",
        "ema(close, 14)",
        "rsi(close, 14)",
        "atr(14)",
        "close + 10",
        "close * 2",
        "sma(ema(close, 10), 5)",
        "(close > 10) and (close < 1000000)",
        "close.change_1h",
        "close.change_pct_1h",
    ],
)
def test_evaluation_parity(sample_dataset, expr_text):
    """
    Test that backends produce the exact same results for standard operations.
    Currently comparing BatchBackend vs BatchBackend to establish the pattern,
    once IncrementalBackend is ready it will be added here.
    """
    from laakhay.ta.expr.algebra.operators import Expression
    from laakhay.ta.expr.compile import compile_to_ir

    expr = Expression(compile_to_ir(expr_text))
    plan = expr._ensure_plan()

    # Backend 1
    backend1 = BatchBackend()
    res1 = backend1.evaluate(plan, sample_dataset)

    # Backend 2 (IncrementalBackend)
    from laakhay.ta.expr.runtime.backends.incremental import IncrementalBackend

    backend2 = IncrementalBackend()
    res2 = backend2.evaluate(plan, sample_dataset)

    if isinstance(res1, dict):
        assert_dict_parity(res1, res2)
    else:
        assert_series_parity(res1, res2)


def test_incremental_replay(sample_dataset):
    """Test that snapshotting the state mid-stream and replaying produces matching output."""
    from decimal import Decimal

    from laakhay.ta.core.types import Price
    from laakhay.ta.expr.algebra.operators import Expression
    from laakhay.ta.expr.compile import compile_to_ir
    from laakhay.ta.expr.runtime.backends.incremental import IncrementalBackend

    expr = Expression(compile_to_ir("sma(close, 14)"))
    plan = expr._ensure_plan()

    backend = IncrementalBackend()
    res_full = backend.evaluate(plan, sample_dataset)

    backend.initialize(plan, sample_dataset)

    ds = sample_dataset
    all_series = [s for _, s in ds]
    timestamps = all_series[0].timestamps
    n_points = len(timestamps)

    mid = n_points // 2

    def create_tick(idx):
        tick = {}
        for k, s in ds:
            if hasattr(s, "to_series"):
                try:
                    tick[f"{k.source}.close"] = s.to_series("close").values[idx]
                    tick["close"] = s.to_series("close").values[idx]
                    tick["high"] = s.to_series("high").values[idx]
                    tick["low"] = s.to_series("low").values[idx]
                    tick["open"] = s.to_series("open").values[idx]
                    tick["volume"] = s.to_series("volume").values[idx]
                except Exception:
                    pass
            else:
                tick[f"{k.source}.{k.source}"] = s.values[idx]
                tick[k.source] = s.values[idx]
        return tick

    # Run first half normally
    for i in range(mid):
        backend.step(plan, create_tick(i))

    # Snapshot at midpoint
    snap = backend.snapshot(plan)

    # Generate events for second half
    events = [create_tick(i) for i in range(mid, n_points)]

    # Replay from midpoint
    replay_results = backend.replay(plan, snap, events)
    replay_vals = tuple(Price(v) if v is not None else Price(Decimal("0")) for v in replay_results)

    # Extracted values from the continuous run
    if isinstance(res_full, dict):
        # get the default series
        res_full_vals = list(res_full.values())[0].values
    else:
        res_full_vals = res_full.values

    # Compare second half values
    assert res_full_vals[mid:] == replay_vals
