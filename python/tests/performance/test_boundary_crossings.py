from __future__ import annotations

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


def test_single_boundary_crossing_for_supported_plan(sample_ohlcv_data, monkeypatch) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    plan = compile_expression("rsi(close, 14)")._ensure_plan()
    backend = IncrementalRustBackend()

    call_count = {"execute_plan_payload": 0}

    import laakhay.ta.expr.execution.backends.incremental_rust as backend_module

    original = backend_module.ta_py.execute_plan_payload

    def wrapped_execute_plan_payload(*args, **kwargs):  # noqa: ANN002, ANN003
        call_count["execute_plan_payload"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(backend_module.ta_py, "execute_plan_payload", wrapped_execute_plan_payload)
    out = backend.evaluate(plan, ds)

    assert out
    assert call_count["execute_plan_payload"] == 1
