from __future__ import annotations

from collections import OrderedDict

import ta_py

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.execution.backends.batch import BatchBackend
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend

from .utils import assert_dict_parity


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


def test_rust_dataset_info_matches_python_surface(sample_ohlcv_data) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    info = ds.rust_info()
    assert info["partition_count"] == 1
    assert info["ohlcv_row_count"] == len(sample_ohlcv_data["timestamps"])
    assert info["series_count"] == 0
    assert info["series_row_count"] == 0


def test_rust_backend_result_parity_on_rust_owned_dataset(sample_ohlcv_data) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    plan = compile_expression("rsi(close, 14)")._ensure_plan()

    py_res = BatchBackend().evaluate(plan, ds)
    rust_res = IncrementalRustBackend().evaluate(plan, ds)

    assert isinstance(py_res, dict)
    assert isinstance(rust_res, dict)
    assert_dict_parity(py_res, rust_res)


def test_execute_plan_output_order_is_deterministic(sample_ohlcv_data) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    requests = [
        OrderedDict(
            node_id=2,
            kernel_id="atr",
            input_field="close",
            kwargs={"period": 14},
        ),
        OrderedDict(
            node_id=1,
            kernel_id="rsi",
            input_field="close",
            kwargs={"period": 14},
        ),
    ]
    out = ta_py.execute_plan(
        ds.rust_dataset_id, sample_ohlcv_data["symbol"], sample_ohlcv_data["timeframe"], "ohlcv", requests
    )
    assert list(out.keys()) == [1, 2]

    out2 = ta_py.execute_plan(
        ds.rust_dataset_id,
        sample_ohlcv_data["symbol"],
        sample_ohlcv_data["timeframe"],
        "ohlcv",
        requests,
    )
    assert list(out2.keys()) == [1, 2]
    assert out[1] == out2[1]
    assert out[2] == out2[2]


def test_snapshot_replay_determinism(sample_ohlcv_data) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    plan = compile_expression("rsi(close, 14)")._ensure_plan()
    backend = IncrementalRustBackend()
    backend.initialize(plan, ds)

    ticks = []
    ohlcv = ds.series(sample_ohlcv_data["symbol"], sample_ohlcv_data["timeframe"], "ohlcv")
    assert isinstance(ohlcv, OHLCV)
    for i in range(len(ohlcv.timestamps)):
        ticks.append(
            {
                "close": float(ohlcv.closes[i]),
                "high": float(ohlcv.highs[i]),
                "low": float(ohlcv.lows[i]),
                "open": float(ohlcv.opens[i]),
                "volume": float(ohlcv.volumes[i]),
            }
        )

    half = len(ticks) // 2
    for i in range(half):
        backend.step(plan, ticks[i], event_index=i + 1)

    snap = backend.snapshot(plan)
    replay_1 = backend.replay(plan, snap, ticks[half:])
    replay_2 = backend.replay(plan, snap, ticks[half:])
    assert replay_1 == replay_2
