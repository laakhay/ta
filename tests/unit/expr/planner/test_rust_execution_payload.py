from __future__ import annotations

from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.planner.manifest import build_rust_execution_payload


def test_build_rust_execution_payload_contains_graph_metadata() -> None:
    plan = compile_expression("sma(20) > sma(50) and rsi(14) > 50")._ensure_plan()
    payload = build_rust_execution_payload(
        plan,
        dataset_id=7,
        symbol="BTCUSDT",
        timeframe="1h",
        source="ohlcv",
        requests=[{"node_id": 1, "kernel_id": "rsi", "input_field": "close", "kwargs": {"period": 14}}],
    )

    assert payload["dataset_id"] == 7
    assert payload["partition"] == {"symbol": "BTCUSDT", "timeframe": "1h", "source": "ohlcv"}
    assert payload["graph"]["root_id"] == int(plan.graph.root_id)
    assert payload["graph"]["node_order"] == [int(n) for n in plan.node_order]
    assert isinstance(payload["graph"]["nodes"], dict)
    assert isinstance(payload["graph"]["edges"], dict)
    assert payload["requests"][0]["kernel_id"] == "rsi"


def test_build_rust_execution_payload_serializes_node_kinds() -> None:
    plan = compile_expression("sma(20) > sma(50)")._ensure_plan()
    payload = build_rust_execution_payload(
        plan,
        dataset_id=1,
        symbol="BTCUSDT",
        timeframe="1h",
        source="ohlcv",
        requests=[],
    )
    kinds = {node["kind"] for node in payload["graph"]["nodes"].values()}
    assert "call" in kinds
    assert "binary_op" in kinds
