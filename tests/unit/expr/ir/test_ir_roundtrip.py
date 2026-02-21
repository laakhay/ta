"""Tests for Canonical IR serialization roundtrip."""

import pytest
from laakhay.ta.expr.ir.nodes import (
    LiteralNode, SourceRefNode, CallNode, BinaryOpNode,
    FilterNode, AggregateNode, TimeShiftNode
)
from laakhay.ta.expr.ir.serialize import ir_to_dict, ir_from_dict

def test_ir_roundtrip_literal():
    node = LiteralNode(value=42.0)
    data = ir_to_dict(node)
    loaded = ir_from_dict(data)
    assert node == loaded

def test_ir_roundtrip_source_ref():
    node = SourceRefNode(symbol="BTC", field="price", source="ohlcv")
    data = ir_to_dict(node)
    loaded = ir_from_dict(data)
    assert node == loaded

def test_ir_roundtrip_call():
    node = CallNode(
        name="sma", 
        args=[SourceRefNode(symbol="BTC", field="price")],
        kwargs={"period": LiteralNode(value=14)}
    )
    data = ir_to_dict(node)
    loaded = ir_from_dict(data)
    assert node == loaded

def test_ir_roundtrip_complex():
    """Test roundtrip of a more complex nested expression."""
    node = BinaryOpNode(
        operator="add",
        left=CallNode(name="sma", kwargs={"period": LiteralNode(value=14)}),
        right=LiteralNode(value=10.0)
    )
    data = ir_to_dict(node)
    loaded = ir_from_dict(data)
    assert node == loaded
