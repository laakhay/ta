from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from laakhay.ta.core.series import Series
from laakhay.ta.expr.execution.runner import evaluate_plan
from laakhay.ta.expr.ir.nodes import LiteralNode
from laakhay.ta.expr.planner.builder import build_graph
from laakhay.ta.expr.planner.planner import compute_plan


@dataclass
class _DummyBackend:
    called: bool = False

    def evaluate(self, plan, data, **options):  # noqa: ANN001
        self.called = True
        return {"plan": plan.graph_hash, "data": data, "options": options}


def _sample_series() -> Series[Any]:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    return Series(
        timestamps=(ts,),
        values=(Decimal("1"),),
        symbol="BTCUSDT",
        timeframe="1h",
    )


def _sample_plan():
    graph = build_graph(LiteralNode(1.0))
    return compute_plan(graph)


def test_evaluate_plan_uses_injected_backend() -> None:
    backend = _DummyBackend()
    plan = _sample_plan()
    data = _sample_series()

    out = evaluate_plan(plan, data, backend=backend, return_all_outputs=True)
    assert backend.called is True
    assert out["plan"] == plan.graph_hash
    assert out["data"] == data
    assert out["options"]["return_all_outputs"] is True
