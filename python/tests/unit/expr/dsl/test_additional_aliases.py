"""Tests for parsing additional aliases added in Commit 9b."""

from laakhay.ta.expr.dsl import parse_expression_text
from laakhay.ta.expr.ir.nodes import CallNode, LiteralNode


def test_alias_parsing_rolling_std():
    expr = parse_expression_text("std(close, 20)")
    assert isinstance(expr, CallNode)
    assert expr.name == "rolling_std"
    assert isinstance(expr.args[1], LiteralNode)
    assert expr.args[1].value == 20

    expr = parse_expression_text("stddev(close, 20)")
    assert expr.name == "rolling_std"


def test_alias_parsing_rolling_sum():
    expr = parse_expression_text("sum(close, 20)")
    assert isinstance(expr, CallNode)
    assert expr.name == "rolling_sum"


def test_alias_parsing_rolling_rma():
    expr = parse_expression_text("rma(close, 14)")
    assert isinstance(expr, CallNode)
    assert expr.name == "rolling_rma"
    assert isinstance(expr.args[1], LiteralNode)
    assert expr.args[1].value == 14


def test_alias_parsing_rolling_argextrema():
    expr = parse_expression_text("argmax(close, 20)")
    assert expr.name == "rolling_argmax"

    expr = parse_expression_text("argmin(close, 20)")
    assert expr.name == "rolling_argmin"


def test_alias_parsing_cumsum():
    expr = parse_expression_text("cumsum(close)")
    assert isinstance(expr, CallNode)
    assert expr.name == "cumulative_sum"


def test_alias_parsing_pos_neg():
    expr = parse_expression_text("pos(close)")
    assert expr.name == "positive_values"

    expr = parse_expression_text("neg(close)")
    assert expr.name == "negative_values"


def test_alias_parsing_tr():
    # tr() since it's a function call
    expr = parse_expression_text("tr()")
    assert isinstance(expr, CallNode)
    assert expr.name == "true_range"
