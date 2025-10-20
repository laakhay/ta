# tests/test_expressions_operators.py
"""Lean, comprehensive tests for laakhay.ta.expressions.operators."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.expressions.models import BinaryOp, Literal, OperatorType, UnaryOp
from laakhay.ta.expressions.operators import Expression, as_expression

UTC = UTC


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def mk_series(
    vals, stamps=None, symbol="BTC", tf="1h"
) -> Series[Price]:
    if stamps is None:
        stamps = (datetime(2024, 1, 1, tzinfo=UTC),)
    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(Price(v) for v in vals),
        symbol=symbol,
        timeframe=tf,
    )


# ---------------------------------------------------------------------
# Expression wrapper
# ---------------------------------------------------------------------

class TestExpression:
    def test_creation_from_literal_series_scalar(self, literal_10, test_series):
        # literal
        expr_lit = Expression(literal_10)
        assert expr_lit._node == literal_10

        # series
        from laakhay.ta.expressions.operators import _to_node
        expr_ser = Expression(_to_node(test_series))
        assert isinstance(expr_ser._node, Literal) and expr_ser._node.value == test_series

        # scalar
        expr_s = Expression(_to_node(42))
        assert isinstance(expr_s._node, Literal) and expr_s._node.value == 42

    def test_evaluate_and_describe_and_deps(self, literal_10, literal_20):
        expr = Expression(literal_10)
        out = expr.evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] == Price(10)

        add = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        ex_add = Expression(add)
        assert ex_add.describe() == "(10 + 20)"
        assert isinstance(ex_add.dependencies(), list)

    @pytest.mark.parametrize(
        "op_type",
        [OperatorType.ADD, OperatorType.SUB, OperatorType.MUL, OperatorType.DIV, OperatorType.MOD, OperatorType.POW],
    )
    def test_arithmetic_overloading(self, literal_10, literal_20, op_type):
        a, b = Expression(literal_10), Expression(literal_20)
        node = {
            OperatorType.ADD: (a + b),
            OperatorType.SUB: (a - b),
            OperatorType.MUL: (a * b),
            OperatorType.DIV: (a / b),
            OperatorType.MOD: (a % b),
            OperatorType.POW: (a ** b),
        }[op_type]._node
        assert isinstance(node, BinaryOp) and node.operator == op_type

    @pytest.mark.parametrize(
        "op_type",
        [OperatorType.EQ, OperatorType.NE, OperatorType.LT, OperatorType.LE, OperatorType.GT, OperatorType.GE],
    )
    def test_comparison_overloading(self, literal_10, literal_20, op_type):
        a, b = Expression(literal_10), Expression(literal_20)
        node = {
            OperatorType.EQ: (a == b),
            OperatorType.NE: (a != b),
            OperatorType.LT: (a < b),
            OperatorType.LE: (a <= b),
            OperatorType.GT: (a > b),
            OperatorType.GE: (a >= b),
        }[op_type]._node
        assert isinstance(node, BinaryOp) and node.operator == op_type

    def test_unary_overloading(self, literal_10):
        expr = Expression(literal_10)
        neg = (-expr)._node
        pos = (+expr)._node
        assert isinstance(neg, UnaryOp) and neg.operator == OperatorType.NEG
        assert isinstance(pos, UnaryOp) and pos.operator == OperatorType.POS

    @pytest.mark.parametrize(
        "op_type",
        [OperatorType.ADD, OperatorType.SUB, OperatorType.MUL, OperatorType.DIV, OperatorType.MOD, OperatorType.POW],
    )
    def test_scalar_ops_wrap_to_binary(self, literal_10, op_type):
        expr = Expression(literal_10)
        node = {
            OperatorType.ADD: (expr + 5),
            OperatorType.SUB: (expr - 5),
            OperatorType.MUL: (expr * 5),
            OperatorType.DIV: (expr / 5),
            OperatorType.MOD: (expr % 5),
            OperatorType.POW: (expr ** 2),
        }[op_type]._node
        assert isinstance(node, BinaryOp) and node.operator == op_type

    def test_chaining_and_eval(self, literal_10, literal_20):
        # (10 + 20) * 10 = 300
        res = ((Expression(literal_10) + Expression(literal_20)) * Expression(literal_10)).evaluate({})
        assert isinstance(res, Series) and len(res) == 1 and res.values[0] == Price(300)

    def test_series_scalar_broadcast(self, multi_point_series):
        expr = as_expression(multi_point_series)

        # add
        res = (expr + 10).evaluate({})
        assert len(res) == len(multi_point_series)
        assert res.symbol == multi_point_series.symbol and res.timeframe == multi_point_series.timeframe
        expected = tuple(v + Price(Decimal("10")) for v in multi_point_series.values)
        assert res.values == expected

        # commutative path (scalar + series)
        res2 = (as_expression(10) + expr).evaluate({})
        assert res2.values == expected

        # mod
        mod_res = (expr % 3).evaluate({})
        assert len(mod_res) == len(multi_point_series) and mod_res.symbol == multi_point_series.symbol

        # pow
        pow_res = (expr ** 2).evaluate({})
        assert pow_res.values == tuple(v ** 2 for v in multi_point_series.values)

    def test_series_comparison_returns_bool_series(self, multi_point_series):
        gt = (as_expression(multi_point_series) > 150).evaluate({})
        assert len(gt) == len(multi_point_series) and gt.symbol == multi_point_series.symbol
        assert gt.values == (False, True)

    def test_mismatched_series_metadata_raises(self, multi_point_series):
        other = Series(
            timestamps=multi_point_series.timestamps,
            values=(Price(Decimal("1")), Price(Decimal("2"))),
            symbol="OTHER",
            timeframe="1s",
        )
        with pytest.raises(ValueError, match="mismatched metadata"):
            (as_expression(multi_point_series) + as_expression(other)).evaluate({})

    def test_misaligned_timestamps_raises(self, multi_point_series):
        shifted = Series(
            timestamps=(multi_point_series.timestamps[0], multi_point_series.timestamps[1] + timedelta(seconds=1)),
            values=(Price(Decimal("1")), Price(Decimal("2"))),
            symbol=multi_point_series.symbol,
            timeframe=multi_point_series.timeframe,
        )
        with pytest.raises(ValueError, match="timestamp alignment"):
            (as_expression(multi_point_series) + as_expression(shifted)).evaluate({})


# ---------------------------------------------------------------------
# as_expression
# ---------------------------------------------------------------------

class TestAsExpression:
    def test_wrap_scalar_series_literal_and_idempotent(self, literal_10, test_series):
        e_s = as_expression(42)
        assert isinstance(e_s, Expression) and isinstance(e_s._node, Literal) and e_s._node.value == 42

        e_ser = as_expression(test_series)
        assert isinstance(e_ser, Expression) and isinstance(e_ser._node, Literal) and e_ser._node.value == test_series

        e_lit = as_expression(literal_10)
        assert isinstance(e_lit, Expression) and e_lit._node == literal_10

        already = Expression(literal_10)
        assert as_expression(already) == already

    def test_operator_chaining(self, literal_10, literal_20):
        res = as_expression(literal_10) + as_expression(literal_20)
        assert isinstance(res, Expression)
        assert isinstance(res._node, BinaryOp) and res._node.operator == OperatorType.ADD
        assert res._node.left == literal_10 and res._node.right == literal_20


# ---------------------------------------------------------------------
# Evaluation edge cases
# ---------------------------------------------------------------------

class TestExpressionEvaluationEdgeCases:
    def test_empty_and_none_context(self, literal_10):
        for ctx in ({}, None):
            out = Expression(literal_10).evaluate(ctx)
            assert isinstance(out, Series) and len(out) == 1 and out.values[0] == Price(10)

    def test_complex_nested_evaluation(self, literal_10, literal_20):
        # ((10 + 20) * 10) - (20 / 10) = 300 - 2 = 298
        expr = ((Expression(literal_10) + Expression(literal_20)) * Expression(literal_10)) - (
            Expression(literal_20) / Expression(literal_10)
        )
        out = expr.evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] == Price(298)

    def test_dependency_tracking_complex(self, literal_10, literal_20):
        deps = ((Expression(literal_10) + Expression(literal_20)) * (Expression(literal_10) - Expression(literal_20))).dependencies()
        assert isinstance(deps, list)


# ---------------------------------------------------------------------
# Financial-critical scenarios
# ---------------------------------------------------------------------

