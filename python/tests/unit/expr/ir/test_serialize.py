"""Tests for IR serialization round-trip preservation."""

import json

from laakhay.ta.expr.ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    FilterNode,
    IndexNode,
    LiteralNode,
    MemberAccessNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
)
from laakhay.ta.expr.ir.serialize import ir_from_dict, ir_to_dict


def assert_roundtrip(node):
    """Utility to assert that a node survives a round-trip perfectly."""
    data = ir_to_dict(node)

    # Verify JSON compatibility (ensure no non-serializable objects)
    json_str = json.dumps(data)
    loaded_data = json.loads(json_str)

    reconstructed = ir_from_dict(loaded_data)

    assert reconstructed == node

    # Explicitly check metadata if present
    if node.span_start is not None:
        assert reconstructed.span_start == node.span_start
    if node.span_end is not None:
        assert reconstructed.span_end == node.span_end
    if node.type_tag != "unknown":
        assert reconstructed.type_tag == node.type_tag


def test_literal_roundtrip():
    assert_roundtrip(LiteralNode(value=10.5))
    assert_roundtrip(LiteralNode(value="test"))
    assert_roundtrip(LiteralNode(value=True))
    assert_roundtrip(LiteralNode(value=42, span_start=10, span_end=12, type_tag="scalar_number"))


def test_source_ref_roundtrip():
    node = SourceRefNode(
        symbol="BTC/USDT",
        field="close",
        source="ohlcv",
        exchange="binance",
        timeframe="1h",
        base="BTC",
        quote="USDT",
        instrument_type="spot",
    )
    assert_roundtrip(node)

    # Minimal version
    assert_roundtrip(SourceRefNode(symbol="ETH/USDT", field="high"))


def test_call_roundtrip():
    node = CallNode(
        name="sma", args=[SourceRefNode(symbol="BTC", field="close")], kwargs={"period": LiteralNode(20)}, output="main"
    )
    assert_roundtrip(node)


def test_binary_op_roundtrip():
    node = BinaryOpNode(operator="add", left=LiteralNode(1), right=LiteralNode(2))
    assert_roundtrip(node)

    # Comparison
    assert_roundtrip(BinaryOpNode("gt", LiteralNode(10), LiteralNode(5)))


def test_unary_op_roundtrip():
    assert_roundtrip(UnaryOpNode("neg", LiteralNode(10)))
    assert_roundtrip(UnaryOpNode("not", LiteralNode(True)))


def test_filter_roundtrip():
    node = FilterNode(
        series=SourceRefNode(symbol="BTC", source="trades", field="price"),
        condition=BinaryOpNode("gt", SourceRefNode(symbol="BTC", source="trades", field="amount"), LiteralNode(100.0)),
    )
    assert_roundtrip(node)


def test_aggregate_roundtrip():
    node = AggregateNode(
        series=SourceRefNode(symbol="BTC", source="trades", field="amount"), operation="sum", field="qty"
    )
    assert_roundtrip(node)

    # Optional field
    assert_roundtrip(AggregateNode(SourceRefNode(symbol="BTC", source="trades", field="price"), "count"))


def test_timeshift_roundtrip():
    node = TimeShiftNode(series=SourceRefNode(symbol="BTC", field="close"), shift="24h", operation="change_pct")
    assert_roundtrip(node)


def test_member_access_roundtrip():
    node = MemberAccessNode(
        expr=CallNode("ichimoku", args=[SourceRefNode(symbol="BTC", field="close")]), member="tenkan_sen"
    )
    assert_roundtrip(node)


def test_index_roundtrip():
    node = IndexNode(expr=LiteralNode([1, 2, 3]), index=LiteralNode(0))
    assert_roundtrip(node)


def test_deep_nested_roundtrip():
    # Complex expression: sma(close, 20) > rsi(close, 14) and volume.sum() > 1000
    expr = BinaryOpNode(
        "and",
        BinaryOpNode(
            "gt",
            CallNode("sma", [SourceRefNode(symbol="BTC", field="close")], {"period": LiteralNode(20)}),
            CallNode("rsi", [SourceRefNode(symbol="BTC", field="close")], {"period": LiteralNode(14)}),
        ),
        BinaryOpNode(
            "gt",
            AggregateNode(SourceRefNode(symbol="BTC", source="trades", field="amount"), "sum"),
            LiteralNode(1000.0),
        ),
    )
    assert_roundtrip(expr)


def test_metadata_preservation():
    node = CallNode(
        name="ema",
        args=[SourceRefNode(symbol="BTC", field="close", span_start=5, span_end=15)],
        kwargs={"period": LiteralNode(50, span_start=20, span_end=22)},
        span_start=0,
        span_end=23,
        type_tag="series_number",
    )
    assert_roundtrip(node)


def test_complex_indicator_outputs():
    """Test CallNode with specific output selector."""
    node = CallNode(
        name="bbands",
        args=[SourceRefNode(symbol="BTC", field="close")],
        kwargs={"period": LiteralNode(20)},
        output="upper",
    )
    assert_roundtrip(node)


def test_nested_metadata_preservation():
    """Verify that metadata is preserved in deep trees."""
    inner = BinaryOpNode(
        "add",
        LiteralNode(10, span_start=1, span_end=2),
        LiteralNode(20, span_start=4, span_end=5),
        span_start=1,
        span_end=5,
        type_tag="scalar_number",
    )
    outer = UnaryOpNode("neg", inner, span_start=0, span_end=5, type_tag="series_number")
    assert_roundtrip(outer)


def test_empty_collections_roundtrip():
    """Ensure empty args/kwargs are preserved precisely."""
    node = CallNode(name="now", args=[], kwargs={})
    assert_roundtrip(node)
