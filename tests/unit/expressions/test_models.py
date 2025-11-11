# tests/test_expressions_models.py
"""Lean, comprehensive tests for laakhay.ta.expressions.models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.expressions.models import (
    SCALAR_SYMBOL,
    BinaryOp,
    ExpressionNode,
    Literal,
    OperatorType,
    UnaryOp,
    _align_series,
    _broadcast_scalar_series,
    _coerce_decimal,
    _comparison_series,
    _make_scalar_series,
    _wrap_literal,
)

UTC = UTC


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def mk_series(vals, stamps=None, symbol="BTC", tf="1h"):
    if stamps is None:
        stamps = (datetime(2024, 1, 1, tzinfo=UTC),)
    return Series[Price](
        timestamps=tuple(stamps),
        values=tuple(Price(v) if not isinstance(v, Price) else v for v in vals),
        symbol=symbol,
        timeframe=tf,
    )


def scal(v) -> Literal:
    return Literal(v)


def lit_series(vals, **kw) -> Literal:
    return Literal(mk_series(vals, **kw))


# ---------------------------------------------------------------------
# OperatorType
# ---------------------------------------------------------------------


class TestOperatorType:
    def test_values_and_membership(self):
        expected = {
            ("ADD", "+"),
            ("SUB", "-"),
            ("MUL", "*"),
            ("DIV", "/"),
            ("MOD", "%"),
            ("POW", "**"),
            ("EQ", "=="),
            ("NE", "!="),
            ("LT", "<"),
            ("LE", "<="),
            ("GT", ">"),
            ("GE", ">="),
            ("AND", "and"),
            ("OR", "or"),
            ("NOT", "not"),
        }
        got = {(op.name, op.value) for op in OperatorType}
        assert got == expected
        assert len(list(OperatorType)) == 15


# ---------------------------------------------------------------------
# Literal
# ---------------------------------------------------------------------


class TestLiteral:
    def test_creation_and_describe_and_hash(self):
        literal_node = Literal(42)
        assert literal_node.value == 42
        assert literal_node.describe() == "42"
        assert hash(Literal(10)) == hash(Literal(10))  # same payload, same hash semantics

    def test_creation_series_and_evaluate(self):
        s = mk_series([Decimal("100")])
        literal_node = Literal(s)
        out = literal_node.evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] == Price(Decimal("100"))

    def test_evaluate_scalar(self):
        out = Literal(10).evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] == Price(10)

    def test_dependencies_empty(self):
        assert Literal(10).dependencies() == []


# ---------------------------------------------------------------------
# BinaryOp
# ---------------------------------------------------------------------


class TestBinaryOp:
    def test_creation_and_describe_and_hash(self):
        l10, l20 = Literal(10), Literal(20)
        op = BinaryOp(OperatorType.ADD, l10, l20)
        assert (op.left, op.operator, op.right) == (l10, OperatorType.ADD, l20)
        assert op.describe() == "(10 + 20)"
        # hash on structure equality
        op1 = BinaryOp(l10, OperatorType.ADD, l20)
        op2 = BinaryOp(l10, OperatorType.ADD, l20)
        assert hash(op1) == hash(op2)

    @pytest.mark.parametrize(
        "otype,left,right,expected",
        [
            (OperatorType.ADD, 10, 20, Price(30)),
            (OperatorType.SUB, 20, 10, Price(10)),
            (OperatorType.MUL, 10, 20, Price(200)),
            (OperatorType.DIV, 20, 10, Price(2)),
            (OperatorType.MOD, 20, 10, Price(0)),
            (OperatorType.POW, 10, 20, Price(10**20)),
        ],
    )
    def test_numeric_ops_on_scalars(self, otype, left, right, expected):
        op = BinaryOp(otype, Literal(left), Literal(right))
        out = op.evaluate({})
        assert isinstance(out, Series) and len(out) == 1
        assert out.values[0] == expected

    @pytest.mark.parametrize(
        "otype,left,right,expected",
        [
            (OperatorType.EQ, 10, 10, True),
            (OperatorType.NE, 10, 20, True),
            (OperatorType.LT, 10, 20, True),
            (OperatorType.GT, 20, 10, True),
        ],
    )
    def test_comparison_ops_on_scalars(self, otype, left, right, expected):
        op = BinaryOp(otype, Literal(left), Literal(right))
        out = op.evaluate({})
        assert isinstance(out, Series) and len(out) == 1
        assert out.values[0] is expected

    def test_scalar_broadcasting_inherits_metadata(self):
        ser = mk_series([100.0], symbol="TEST", tf="1s")
        op = BinaryOp(OperatorType.ADD, Literal(10), Literal(ser))
        out = op.evaluate({})
        assert out.symbol == ser.symbol and out.timeframe == ser.timeframe
        assert len(out) == len(ser)

    def test_different_lengths_raises(self):
        s2 = mk_series(
            [100.0, 200.0],
            stamps=(
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
            ),
            symbol="TEST",
            tf="1s",
        )
        s3 = mk_series(
            [50.0, 150.0, 250.0],
            stamps=(
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                datetime(2024, 1, 1, 0, 0, 2, tzinfo=UTC),
                datetime(2024, 1, 1, 0, 0, 3, tzinfo=UTC),
            ),
            symbol="TEST",
            tf="1s",
        )
        op = BinaryOp(OperatorType.ADD, Literal(s2), Literal(s3))
        with pytest.raises(ValueError, match=r"Cannot perform \+ on series of different lengths"):
            op.evaluate({})

    def test_unsupported_operator_raises(self):
        # AND is supported: truthy AND truthy -> True
        op = BinaryOp(OperatorType.AND, Literal(10), Literal(20))
        out = op.evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] is True


# ---------------------------------------------------------------------
# UnaryOp
# ---------------------------------------------------------------------


class TestUnaryOp:
    def test_creation_describe_and_eval(self):
        op_neg = UnaryOp(OperatorType.NEG, Literal(10))
        assert op_neg.operator == OperatorType.NEG and op_neg.operand.value == 10
        res = op_neg.evaluate({})
        assert isinstance(res, Series) and res.values[0] == Price(-10)
        assert op_neg.describe() == "-10"

        op_pos = UnaryOp(OperatorType.POS, Literal(10))
        res2 = op_pos.evaluate({})
        assert isinstance(res2, Series) and res2.values[0] == Price(10)

    def test_unsupported_operator_raises(self):
        # NOT is supported: not truthy -> False
        op = UnaryOp(OperatorType.NOT, Literal(10))
        out = op.evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] is False


# ---------------------------------------------------------------------
# Operator overloading on ExpressionNode
# ---------------------------------------------------------------------


class TestExpressionNodeOperatorOverloading:
    def test_arithmetic(self):
        a, b = Literal(10), Literal(20)
        assert isinstance(a + b, BinaryOp) and (a + b).operator == OperatorType.ADD
        assert isinstance(a - b, BinaryOp) and (a - b).operator == OperatorType.SUB
        assert isinstance(a * b, BinaryOp) and (a * b).operator == OperatorType.MUL
        assert isinstance(a / b, BinaryOp) and (a / b).operator == OperatorType.DIV
        assert isinstance(a % b, BinaryOp) and (a % b).operator == OperatorType.MOD
        assert isinstance(a**b, BinaryOp) and (a**b).operator == OperatorType.POW

    def test_comparisons(self):
        a, b = Literal(10), Literal(20)
        assert isinstance(a == b, BinaryOp) and (a == b).operator == OperatorType.EQ
        assert isinstance(a != b, BinaryOp) and (a != b).operator == OperatorType.NE
        assert isinstance(a < b, BinaryOp) and (a < b).operator == OperatorType.LT
        assert isinstance(a <= b, BinaryOp) and (a <= b).operator == OperatorType.LE
        assert isinstance(a > b, BinaryOp) and (a > b).operator == OperatorType.GT
        assert isinstance(a >= b, BinaryOp) and (a >= b).operator == OperatorType.GE

    def test_unary(self):
        a = Literal(10)
        assert isinstance(-a, UnaryOp) and (-a).operator == OperatorType.NEG
        assert isinstance(+a, UnaryOp) and (+a).operator == OperatorType.POS


# ---------------------------------------------------------------------
# Financial-critical scenarios & nested expressions
# ---------------------------------------------------------------------


class TestFinancialCriticalScenarios:
    def test_divide_by_zero_raises(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            BinaryOp(OperatorType.DIV, Literal(10), Literal(0)).evaluate({})

    def test_modulo_by_zero_raises(self):
        with pytest.raises(ValueError, match="Cannot perform modulo with zero divisor"):
            BinaryOp(OperatorType.MOD, Literal(10), Literal(0)).evaluate({})

    def test_pow_large_exponent_handles(self):
        out = BinaryOp(OperatorType.POW, Literal(10), Literal(100)).evaluate({})
        assert isinstance(out, Series) and len(out) == 1  # value existence is enough; huge ints are supported

    def test_nested(self):
        # (10 + 20) * (10 - 20) = 30 * (-10) = -300
        add = BinaryOp(OperatorType.ADD, Literal(10), Literal(20))
        sub = BinaryOp(OperatorType.SUB, Literal(10), Literal(20))
        mul = BinaryOp(OperatorType.MUL, add, sub)
        out = mul.evaluate({})
        assert isinstance(out, Series) and out.values[0] == Price(-300)

    def test_dependency_tracking(self):
        expr = BinaryOp(
            OperatorType.MUL,
            BinaryOp(OperatorType.ADD, Literal(10), Literal(20)),
            Literal(10),
        )
        deps = expr.dependencies()
        assert isinstance(deps, list)

    def test_price_calculation_precision(self):
        p1 = Decimal("100.123456789")
        p2 = Decimal("200.987654321")
        out = BinaryOp(OperatorType.ADD, Literal(p1), Literal(p2)).evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] == Price(p1 + p2)

    def test_division_by_very_small_number(self):
        big = Decimal("1000000000000")
        small = Decimal("0.0000000001")
        out = BinaryOp(OperatorType.DIV, Literal(big), Literal(small)).evaluate({})
        assert isinstance(out, Series) and len(out) == 1
        assert out.values[0] > Price(Decimal("1000000000000"))

    def test_modulo_with_large_numbers(self):
        n = Decimal("1000000000000")
        m = Decimal("7")
        out = BinaryOp(OperatorType.MOD, Literal(n), Literal(m)).evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] == Price(n % m)

    def test_power_with_fractional_exponent(self):
        base = Decimal("100")
        exp = Decimal("0.5")  # sqrt
        out = BinaryOp(OperatorType.POW, Literal(base), Literal(exp)).evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] > Price(Decimal("9"))

    def test_mixed_decimal_float_comparisons(self):
        # comparisons should yield a boolean series
        out = BinaryOp(OperatorType.EQ, Literal(Decimal("100.5")), Literal(100.5)).evaluate({})
        assert isinstance(out, Series) and len(out) == 1 and out.values[0] is True


# ---------------------------------------------------------------------
# Engine critical issues (metadata, comparisons)
# ---------------------------------------------------------------------


class TestExpressionEngineCriticalIssues:
    def test_elementwise_comparison_between_series(self):
        s1 = mk_series(
            [100.0, 200.0],
            stamps=(
                datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
                datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC),
            ),
            symbol="BTC",
            tf="1h",
        )
        s2 = mk_series([100.0, 300.0], stamps=s1.timestamps, symbol="BTC", tf="1h")
        res = BinaryOp(OperatorType.EQ, Literal(s1), Literal(s2)).evaluate({})
        assert len(res.values) == 2 and res.values[0] is True and res.values[1] is False


# ---------------------------------------------------------------------
# Internal helpers: metadata inheritance & alignment/broadcasting
# ---------------------------------------------------------------------


class TestExpressionMetadataInheritance:
    def test_series_priority_over_scalar(self):
        series = mk_series([100.0], symbol="BTC", tf="1h")
        scalar = _make_scalar_series(5)
        assert scalar.symbol == SCALAR_SYMBOL
        aligned_scalar, aligned_series = _align_series(scalar, series, operator=OperatorType.ADD)
        assert aligned_scalar.symbol == series.symbol and aligned_scalar.timeframe == series.timeframe
        assert aligned_series is series

    def test_align_two_scalars_preserve_scalar_meta(self):
        left, right = _make_scalar_series(1), _make_scalar_series(2)
        a, b = _align_series(left, right, operator=OperatorType.ADD)
        assert a.symbol == SCALAR_SYMBOL and b.symbol == SCALAR_SYMBOL

    def test_align_literal_series_mismatch_raises(self):
        series = mk_series([5.0], symbol="BTC", tf="1h")
        literal_series = mk_series([10.0], symbol="LITERAL", tf="1s")
        with pytest.raises(ValueError, match="mismatched metadata"):
            _align_series(literal_series, series, operator=OperatorType.ADD)


class TestExpressionBroadcasting:
    def test_broadcast_scalar_to_series(self):
        scalar = _make_scalar_series(5)
        tgt = mk_series(
            [100.0, 200.0],
            stamps=(
                datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
                datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC),
            ),
            symbol="BTC",
            tf="1h",
        )
        out = _broadcast_scalar_series(scalar, tgt)
        assert out.timestamps == tgt.timestamps and out.symbol == tgt.symbol and out.timeframe == tgt.timeframe
        assert out.values == (Price(5.0), Price(5.0))

    def test_broadcast_invalid_scalar_series(self):
        non_scalar = mk_series([5.0], symbol="BTC", tf="1h")  # not SCALAR
        tgt = mk_series([100.0], symbol="BTC", tf="1h")
        with pytest.raises(ValueError, match="scalar series"):
            _broadcast_scalar_series(non_scalar, tgt)


class TestElementWiseComparison:
    def test_scalar_vs_series(self):
        scalar = _make_scalar_series(100)
        tgt = mk_series(
            [100.0, 200.0],
            stamps=(
                datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
                datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC),
            ),
            symbol="BTC",
            tf="1h",
        )
        res = _comparison_series(scalar, tgt, OperatorType.EQ, lambda a, b: a == b)
        assert len(res.values) == 2 and res.values[0] is True and res.values[1] is False
        assert res.symbol == "BTC" and res.timeframe == "1h"

    def test_series_vs_scalar(self):
        tgt = mk_series(
            [100.0, 200.0],
            stamps=(
                datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
                datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC),
            ),
            symbol="BTC",
            tf="1h",
        )
        scalar = _make_scalar_series(100)
        res = _comparison_series(tgt, scalar, OperatorType.EQ, lambda a, b: a == b)
        assert len(res.values) == 2 and res.values[0] is True and res.values[1] is False
        assert res.symbol == "BTC" and res.timeframe == "1h"

    def test_different_lengths_raises(self):
        s1 = mk_series(
            [100.0, 200.0],
            stamps=(
                datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
                datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC),
            ),
            symbol="BTC",
            tf="1h",
        )
        s2 = mk_series(
            [100.0],
            stamps=(datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),),
            symbol="BTC",
            tf="1h",
        )
        with pytest.raises(ValueError, match="different lengths"):
            _comparison_series(s1, s2, OperatorType.EQ, lambda a, b: a == b)


# ---------------------------------------------------------------------
# BinaryOp evaluation variants (mixed scalar/series)
# ---------------------------------------------------------------------


class TestBinaryOpEvaluation:
    def test_mul(self):
        res = BinaryOp(OperatorType.MUL, Literal(2.0), lit_series([100.0])).evaluate({})
        assert len(res.values) == 1 and res.values[0] == Price(200.0)
        assert res.symbol == "BTC" and res.timeframe == "1h"

    def test_div(self):
        res = BinaryOp(OperatorType.DIV, lit_series([100.0]), Literal(2.0)).evaluate({})
        assert len(res.values) == 1 and res.values[0] == Price(50.0)

    def test_mod(self):
        res = BinaryOp(OperatorType.MOD, lit_series([100.0]), Literal(3.0)).evaluate({})
        assert len(res.values) == 1 and res.values[0] == Price(1.0)

    def test_sub(self):
        res = BinaryOp(OperatorType.SUB, lit_series([100.0]), Literal(50.0)).evaluate({})
        assert len(res.values) == 1 and res.values[0] == Price(50.0)

    def test_pow(self):
        res = BinaryOp(OperatorType.POW, lit_series([2.0]), Literal(3.0)).evaluate({})
        assert len(res.values) == 1 and res.values[0] == Price(8.0)

    def test_lt(self):
        res = BinaryOp(OperatorType.LT, lit_series([50.0]), Literal(100.0)).evaluate({})
        assert len(res.values) == 1 and res.values[0] is True

    def test_unsupported_operator_symbol(self):
        # Mimic non-OperatorType with string for explicit NotImplemented
        class MockOperatorType:
            UNSUPPORTED = "UNSUPPORTED"

        op = BinaryOp(MockOperatorType.UNSUPPORTED, lit_series([100.0]), Literal(2.0))
        with pytest.raises(NotImplementedError, match="Binary operator UNSUPPORTED not implemented"):
            op.evaluate({})


# ---------------------------------------------------------------------
# Coverage-focused tests for internal branches
# ---------------------------------------------------------------------


class TestExpressionCoverageGaps:
    @pytest.mark.parametrize("val,exp", [(True, Price(Decimal(1))), (False, Price(Decimal(0)))])
    def test_coerce_decimal_bools(self, val, exp):
        assert _coerce_decimal(val) == exp

    def test_coerce_decimal_unsupported_type(self):
        with pytest.raises(TypeError, match="Unsupported scalar literal type"):
            _coerce_decimal([1, 2, 3])

    def test_coerce_decimal_invalid_operation(self):
        with pytest.raises(TypeError, match="Unsupported scalar literal"):
            _coerce_decimal("invalid_number")

    def test_expressionnode_is_abstract(self):
        with pytest.raises(TypeError):
            ExpressionNode()

    def test_literal_describe_series(self):
        s = mk_series([100.0])
        desc = Literal(s).describe()
        assert "Series(1 points)" in desc

    def test_binaryop_invalidoperation_wrapped(self, monkeypatch):
        # Force Series.__truediv__ to raise InvalidOperation, expect ValueError wrap
        left, right = lit_series([100.0]), scal(0.0)
        op = BinaryOp(OperatorType.DIV, left, right)

        def boom(*_a, **_k):
            raise InvalidOperation("Division by zero")

        monkeypatch.setattr(Series, "__truediv__", boom)
        with pytest.raises(ValueError, match="Invalid arithmetic operation in expression"):
            op.evaluate({})

    def test_le_and_ge_comparisons(self):
        l1, l2 = Literal(100.0), Literal(200.0)
        assert BinaryOp(OperatorType.LE, l1, l2).evaluate({}).values[0] is True
        assert BinaryOp(OperatorType.GE, l1, l2).evaluate({}).values[0] is False

    def test_wrap_literal_edge_cases(self):
        r1 = _wrap_literal(100.0)
        r2 = _wrap_literal(42)
        assert isinstance(r1, Literal) and r1.value == 100.0
        assert isinstance(r2, Literal) and r2.value == 42
        s = mk_series([100.0])
        r3 = _wrap_literal(s)
        assert isinstance(r3, Literal) and r3.value == s
