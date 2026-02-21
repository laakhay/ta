"""Tests for IR normalize."""

import pytest
from laakhay.ta.expr.ir.nodes import LiteralNode
from laakhay.ta.expr.normalize.normalize import normalize_expression

def test_normalize_identity():
    """Currently normalize is an identity function placeholder."""
    node = LiteralNode(value=42.0)
    assert normalize_expression(node) is node
