from __future__ import annotations

from typing import Any

from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.core.series import Series
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend


def _build_dataset(sample_ohlcv_data: dict[str, Any]) -> Dataset:
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


def test_evaluate_uses_execute_plan_for_supported_root(sample_ohlcv_data, monkeypatch) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    expr = compile_expression("rsi(close, 2)")
    plan = expr._ensure_plan()
    backend = IncrementalRustBackend()

    called: dict[str, Any] = {}

    def fake_execute_plan_payload(payload):  # noqa: ANN001
        called["dataset_id"] = payload["dataset_id"]
        called["symbol"] = payload["partition"]["symbol"]
        called["timeframe"] = payload["partition"]["timeframe"]
        called["source"] = payload["partition"]["source"]
        called["requests"] = payload["requests"]
        return {int(plan.graph.root_id): [42.0] * len(sample_ohlcv_data["timestamps"])}

    monkeypatch.setattr(
        "laakhay.ta.expr.execution.backends.incremental_rust.ta_py.execute_plan_payload",
        fake_execute_plan_payload,
    )

    out = backend.evaluate(plan, ds)
    assert isinstance(out, dict)
    assert called["dataset_id"] == ds.rust_dataset_id
    assert called["source"] == "ohlcv"
    result_series = next(iter(out.values()))
    assert len(result_series.values) == len(sample_ohlcv_data["timestamps"])


def test_evaluate_falls_back_to_batch_for_non_supported_root(sample_ohlcv_data, monkeypatch) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    expr = compile_expression("close + 1")
    plan = expr._ensure_plan()
    backend = IncrementalRustBackend()

    def fake_batch_evaluate(self, plan_arg, dataset_arg, symbol=None, timeframe=None, **options):  # noqa: ANN001
        return Series[Any](
            timestamps=sample_ohlcv_data["timestamps"],
            values=tuple([1.0] * len(sample_ohlcv_data["timestamps"])),
            symbol=sample_ohlcv_data["symbol"],
            timeframe=sample_ohlcv_data["timeframe"],
        )

    monkeypatch.setattr(
        "laakhay.ta.expr.execution.backends.batch.BatchBackend.evaluate",
        fake_batch_evaluate,
    )

    out = backend.evaluate(plan, ds)
    assert isinstance(out, Series)


def test_evaluate_uses_execute_plan_for_vwap_root(sample_ohlcv_data, monkeypatch) -> None:
    ds = _build_dataset(sample_ohlcv_data)
    expr = compile_expression("vwap()")
    plan = expr._ensure_plan()
    backend = IncrementalRustBackend()

    called = {"count": 0}

    def fake_execute_plan_payload(payload):  # noqa: ANN001
        called["count"] += 1
        return {int(plan.graph.root_id): [1.0] * len(sample_ohlcv_data["timestamps"])}

    monkeypatch.setattr(
        "laakhay.ta.expr.execution.backends.incremental_rust.ta_py.execute_plan_payload",
        fake_execute_plan_payload,
    )

    out = backend.evaluate(plan, ds)
    assert isinstance(out, dict)
    assert called["count"] == 1
