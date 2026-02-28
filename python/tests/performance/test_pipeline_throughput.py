from __future__ import annotations

import time

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend


def _build_dataset(sample_ohlcv_data) -> Dataset:
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
    ds = Dataset()
    ds.add_series(ohlcv.symbol, ohlcv.timeframe, ohlcv, "ohlcv")
    return ds


def test_pipeline_throughput_rsi_smoke(sample_ohlcv_data) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    plan = compile_expression("rsi(close, 14)")._ensure_plan()
    backend = IncrementalRustBackend()

    runs = 100
    started = time.perf_counter()
    for _ in range(runs):
        out = backend.evaluate(plan, ds)
        assert out
    elapsed = time.perf_counter() - started

    # Lenient CI guard to catch catastrophic regressions only.
    assert elapsed < 2.0, f"rsi throughput regression: {runs} runs took {elapsed:.4f}s"
