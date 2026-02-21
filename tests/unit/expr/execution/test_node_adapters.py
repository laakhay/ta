from datetime import UTC, datetime
from decimal import Decimal

from laakhay.ta.core.series import Series
from laakhay.ta.expr.execution.node_adapters import eval_binary_step, eval_literal_step, eval_source_ref_step
from laakhay.ta.expr.ir.nodes import BinaryOpNode, LiteralNode, SourceRefNode


def test_eval_source_ref_step_prefers_source_field_key() -> None:
    node = SourceRefNode(symbol=None, field="close", source="ohlcv")
    tick = {"ohlcv.close": Decimal("100"), "close": Decimal("99")}
    assert eval_source_ref_step(node, tick) == Decimal("100")


def test_eval_source_ref_step_falls_back_to_field_key() -> None:
    node = SourceRefNode(symbol=None, field="close", source="ohlcv")
    tick = {"close": Decimal("101")}
    assert eval_source_ref_step(node, tick) == Decimal("101")


def test_eval_source_ref_step_returns_none_when_missing() -> None:
    node = SourceRefNode(symbol=None, field="close", source="ohlcv")
    assert eval_source_ref_step(node, {"open": Decimal("1")}) is None


def test_eval_literal_step_scalar_string_and_none() -> None:
    assert eval_literal_step(LiteralNode(10)) == Decimal("10")
    assert eval_literal_step(LiteralNode("close")) == "close"
    assert eval_literal_step(LiteralNode(None)) is None


def test_eval_literal_step_series_singleton() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    series = Series(
        timestamps=(ts,),
        values=(Decimal("12.5"),),
        symbol="BTCUSDT",
        timeframe="1h",
    )
    out = eval_literal_step(LiteralNode(series))
    assert out == Decimal("12.5")


def test_eval_binary_step_arithmetic_and_comparisons() -> None:
    add = BinaryOpNode("add", LiteralNode(1), LiteralNode(2))
    div = BinaryOpNode("div", LiteralNode(1), LiteralNode(2))
    gt = BinaryOpNode("gt", LiteralNode(2), LiteralNode(1))
    eq = BinaryOpNode("eq", LiteralNode(2), LiteralNode(2))

    assert eval_binary_step(add, [Decimal("2"), Decimal("3")]) == Decimal("5")
    assert eval_binary_step(div, [Decimal("6"), Decimal("0")]) == Decimal("0")
    assert eval_binary_step(gt, [Decimal("2"), Decimal("1")]) == Decimal("1")
    assert eval_binary_step(eq, [Decimal("2"), Decimal("3")]) == Decimal("0")


def test_eval_binary_step_handles_missing_inputs() -> None:
    node = BinaryOpNode("mul", LiteralNode(1), LiteralNode(2))
    assert eval_binary_step(node, [Decimal("2"), None]) is None
    assert eval_binary_step(node, [Decimal("2")]) is None
