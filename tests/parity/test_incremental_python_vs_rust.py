from __future__ import annotations

import math
from typing import Any

import pytest

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.execution.backends.incremental import IncrementalBackend
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend

from .utils import assert_dict_parity, assert_series_parity


@pytest.fixture
def sample_dataset(sample_ohlcv_data) -> Dataset:
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
    ds = Dataset()
    ds.add_series(ohlcv.symbol, ohlcv.timeframe, ohlcv, "ohlcv")
    return ds


def _create_tick(ds: Dataset, idx: int) -> dict[str, Any]:
    tick: dict[str, Any] = {}
    for k, s in ds:
        if hasattr(s, "to_series"):
            tick[f"{k.source}.close"] = s.to_series("close").values[idx]
            tick["close"] = s.to_series("close").values[idx]
            tick["high"] = s.to_series("high").values[idx]
            tick["low"] = s.to_series("low").values[idx]
            tick["open"] = s.to_series("open").values[idx]
            tick["volume"] = s.to_series("volume").values[idx]
            continue
        tick[f"{k.source}.{k.source}"] = s.values[idx]
        tick[k.source] = s.values[idx]
    return tick


@pytest.mark.parametrize("expr_text", ["rsi(close, 14)", "atr(14)"])
def test_incremental_python_vs_rust_evaluate_parity(sample_dataset: Dataset, expr_text: str) -> None:
    plan = compile_expression(expr_text)._ensure_plan()

    py_res = IncrementalBackend().evaluate(plan, sample_dataset)
    rust_res = IncrementalRustBackend().evaluate(plan, sample_dataset)

    if isinstance(py_res, dict):
        assert_dict_parity(py_res, rust_res)
        return
    assert_series_parity(py_res, rust_res)


def test_incremental_python_vs_rust_replay_parity(sample_dataset: Dataset) -> None:
    plan = compile_expression("rsi(close, 14)")._ensure_plan()
    py_backend = IncrementalBackend()
    rust_backend = IncrementalRustBackend()
    py_backend.initialize(plan, sample_dataset)
    rust_backend.initialize(plan, sample_dataset)

    all_series = [s for _, s in sample_dataset]
    n_points = len(all_series[0].timestamps)
    mid = n_points // 2

    for i in range(mid):
        tick = _create_tick(sample_dataset, i)
        py_backend.step(plan, tick, event_index=i + 1)
        rust_backend.step(plan, tick, event_index=i + 1)

    py_snap = py_backend.snapshot(plan)
    rust_snap = rust_backend.snapshot(plan)
    events = [_create_tick(sample_dataset, i) for i in range(mid, n_points)]

    py_replay = py_backend.replay(plan, py_snap, events)
    rust_replay = rust_backend.replay(plan, rust_snap, events)
    assert len(py_replay) == len(rust_replay)
    for lhs, rhs in zip(py_replay, rust_replay, strict=True):
        lhs_missing = lhs is None or (isinstance(lhs, float) and math.isnan(lhs)) or (hasattr(lhs, "is_nan") and lhs.is_nan())
        rhs_missing = rhs is None or (isinstance(rhs, float) and math.isnan(rhs))
        if lhs_missing and rhs_missing:
            continue
        assert lhs == pytest.approx(rhs, rel=1e-9, abs=1e-9)
