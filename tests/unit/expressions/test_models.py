"""Consolidated expressions models tests - lean and efficient."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.expressions.models import ExpressionNode, Literal, BinaryOp, UnaryOp, OperatorType
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price


class TestOperatorType:
    """OperatorType enum tests."""
    
    def test_operator_type_values(self):
        """Test OperatorType enum values."""
        assert OperatorType.ADD.value == "+"
        assert OperatorType.SUB.value == "-"
        assert OperatorType.MUL.value == "*"
        assert OperatorType.DIV.value == "/"
        assert OperatorType.MOD.value == "%"
        assert OperatorType.POW.value == "**"
        assert OperatorType.EQ.value == "=="
        assert OperatorType.NE.value == "!="
        assert OperatorType.LT.value == "<"
        assert OperatorType.LE.value == "<="
        assert OperatorType.GT.value == ">"
        assert OperatorType.GE.value == ">="
        assert OperatorType.AND.value == "and"
        assert OperatorType.OR.value == "or"
        assert OperatorType.NOT.value == "not"
    
    def test_operator_type_enumeration(self):
        """Test OperatorType enumeration."""
        operators = list(OperatorType)
        assert len(operators) == 15
        
        expected_names = {
            "ADD", "SUB", "MUL", "DIV", "MOD", "POW",
            "EQ", "NE", "LT", "LE", "GT", "GE",
            "AND", "OR", "NOT"
        }
        actual_names = {op.name for op in operators}
        assert actual_names == expected_names


class TestLiteral:
    """Literal expression node tests."""
    
    def test_creation_scalar(self):
        """Test Literal creation with scalar value."""
        literal = Literal(42)
        assert literal.value == 42
    
    def test_creation_series(self, test_series):
        """Test Literal creation with series value."""
        literal = Literal(test_series)
        assert literal.value == test_series
    
    def test_evaluate_scalar(self, literal_10):
        """Test Literal evaluation with scalar."""
        context = {}
        result = literal_10.evaluate(context)
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(10)
    
    def test_evaluate_series(self, literal_series):
        """Test Literal evaluation with series."""
        context = {}
        result = literal_series.evaluate(context)
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(Decimal("100"))
    
    def test_dependencies(self, literal_10):
        """Test Literal dependencies."""
        deps = literal_10.dependencies()
        assert deps == []
    
    def test_describe(self, literal_10):
        """Test Literal description."""
        desc = literal_10.describe()
        assert desc == "10"
    
    def test_hash(self, literal_10):
        """Test Literal hash."""
        literal2 = Literal(10)
        assert hash(literal_10) == hash(literal2)


class TestBinaryOp:
    """BinaryOp expression node tests."""
    
    def test_creation(self, literal_10, literal_20):
        """Test BinaryOp creation."""
        op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        assert op.left == literal_10
        assert op.operator == OperatorType.ADD
        assert op.right == literal_20
    
    def test_evaluate_addition(self, literal_10, literal_20):
        """Test BinaryOp evaluation with addition."""
        op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(30)  # 10 + 20
    
    def test_evaluate_subtraction(self, literal_10, literal_20):
        """Test BinaryOp evaluation with subtraction."""
        op = BinaryOp(OperatorType.SUB, literal_20, literal_10)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(10)  # 20 - 10
    
    def test_evaluate_multiplication(self, literal_10, literal_20):
        """Test BinaryOp evaluation with multiplication."""
        op = BinaryOp(OperatorType.MUL, literal_10, literal_20)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(200)  # 10 * 20
    
    def test_evaluate_division(self, literal_20, literal_10):
        """Test BinaryOp evaluation with division."""
        op = BinaryOp(OperatorType.DIV, literal_20, literal_10)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(2)  # 20 / 10
    
    def test_evaluate_modulo(self, literal_20, literal_10):
        """Test BinaryOp evaluation with modulo."""
        op = BinaryOp(OperatorType.MOD, literal_20, literal_10)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(0)  # 20 % 10 = 0
    
    def test_evaluate_power(self, literal_10, literal_20):
        """Test BinaryOp evaluation with power."""
        op = BinaryOp(OperatorType.POW, literal_10, literal_20)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(100000000000000000000)  # 10^20
    
    def test_evaluate_comparison_eq(self, literal_10, literal_20):
        """Test BinaryOp evaluation with equality comparison."""
        op = BinaryOp(OperatorType.EQ, literal_10, literal_10)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(1)  # 10 == 10 = True
    
    def test_evaluate_comparison_ne(self, literal_10, literal_20):
        """Test BinaryOp evaluation with inequality comparison."""
        op = BinaryOp(OperatorType.NE, literal_10, literal_20)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(1)  # 10 != 20 = True
    
    def test_evaluate_comparison_lt(self, literal_10, literal_20):
        """Test BinaryOp evaluation with less than comparison."""
        op = BinaryOp(OperatorType.LT, literal_10, literal_20)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(1)  # 10 < 20 = True
    
    def test_evaluate_comparison_gt(self, literal_10, literal_20):
        """Test BinaryOp evaluation with greater than comparison."""
        op = BinaryOp(OperatorType.GT, literal_20, literal_10)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(1)  # 20 > 10 = True
    
    def test_evaluate_scalar_broadcasting(self, literal_10, multi_point_series):
        """Test BinaryOp scalar broadcasting - expect symbol mismatch error."""
        literal_series = Literal(multi_point_series)
        op = BinaryOp(OperatorType.ADD, literal_series, literal_10)
        # This should raise an error due to symbol mismatch
        with pytest.raises(ValueError, match="Cannot add series with different symbols or timeframes"):
            op.evaluate({})
    
    def test_evaluate_different_lengths_error(self, literal_series, multi_point_series):
        """Test BinaryOp with different lengths raises error."""
        literal_multi = Literal(multi_point_series)
        # Create a series with different length (3 points instead of 2)
        timestamp3 = datetime(2024, 1, 1, 0, 0, 2, tzinfo=timezone.utc)
        timestamp4 = datetime(2024, 1, 1, 0, 0, 3, tzinfo=timezone.utc)
        different_series = Series(
            timestamps=(datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc), timestamp3, timestamp4),
            values=(Price(Decimal("50")), Price(Decimal("150")), Price(Decimal("250"))),
            symbol="TEST",
            timeframe="1s"
        )
        literal_different = Literal(different_series)
        
        op = BinaryOp(OperatorType.ADD, literal_multi, literal_different)
        with pytest.raises(ValueError, match="Cannot perform \\+ operation on series of different lengths"):
            op.evaluate({})
    
    def test_evaluate_unsupported_operator(self, literal_10, literal_20):
        """Test BinaryOp with unsupported operator raises error."""
        op = BinaryOp(OperatorType.AND, literal_10, literal_20)
        with pytest.raises(NotImplementedError, match="Binary operator OperatorType.AND not implemented"):
            op.evaluate({})
    
    def test_dependencies(self, literal_10, literal_20):
        """Test BinaryOp dependencies."""
        op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        deps = op.dependencies()
        assert isinstance(deps, list)
    
    def test_describe(self, literal_10, literal_20):
        """Test BinaryOp description."""
        op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        desc = op.describe()
        assert desc == "(10 + 20)"
    
    def test_hash(self, literal_10, literal_20):
        """Test BinaryOp hash."""
        op1 = BinaryOp(literal_10, OperatorType.ADD, literal_20)
        op2 = BinaryOp(literal_10, OperatorType.ADD, literal_20)
        assert hash(op1) == hash(op2)


class TestUnaryOp:
    """UnaryOp expression node tests."""
    
    def test_creation(self, literal_10):
        """Test UnaryOp creation."""
        op = UnaryOp(OperatorType.NEG, literal_10)
        assert op.operator == OperatorType.NEG
        assert op.operand == literal_10
    
    def test_evaluate_negation(self, literal_10):
        """Test UnaryOp evaluation with negation."""
        op = UnaryOp(OperatorType.NEG, literal_10)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(-10)  # -10
    
    def test_evaluate_positive(self, literal_10):
        """Test UnaryOp evaluation with positive."""
        op = UnaryOp(OperatorType.POS, literal_10)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(10)  # +10
    
    def test_evaluate_unsupported_operator(self, literal_10):
        """Test UnaryOp with unsupported operator raises error."""
        op = UnaryOp(OperatorType.NOT, literal_10)
        with pytest.raises(NotImplementedError, match="Unary operator OperatorType.NOT not implemented"):
            op.evaluate({})
    
    def test_dependencies(self, literal_10):
        """Test UnaryOp dependencies."""
        op = UnaryOp(OperatorType.NEG, literal_10)
        deps = op.dependencies()
        assert isinstance(deps, list)
    
    def test_describe(self, literal_10):
        """Test UnaryOp description."""
        op = UnaryOp(OperatorType.NEG, literal_10)
        desc = op.describe()
        assert desc == "-10"
    
    def test_hash(self, literal_10):
        """Test UnaryOp hash."""
        op1 = UnaryOp(OperatorType.NEG, literal_10)
        op2 = UnaryOp(OperatorType.NEG, literal_10)
        assert hash(op1) == hash(op2)


class TestExpressionNodeOperatorOverloading:
    """ExpressionNode operator overloading tests."""
    
    def test_arithmetic_operators(self, literal_10, literal_20):
        """Test ExpressionNode arithmetic operator overloading."""
        # Addition
        result = literal_10 + literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.ADD
        
        # Subtraction
        result = literal_10 - literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.SUB
        
        # Multiplication
        result = literal_10 * literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.MUL
        
        # Division
        result = literal_10 / literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.DIV
        
        # Modulo
        result = literal_10 % literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.MOD
        
        # Power
        result = literal_10 ** literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.POW
    
    def test_comparison_operators(self, literal_10, literal_20):
        """Test ExpressionNode comparison operator overloading."""
        # Equality
        result = literal_10 == literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.EQ
        
        # Inequality
        result = literal_10 != literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.NE
        
        # Less than
        result = literal_10 < literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.LT
        
        # Less than or equal
        result = literal_10 <= literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.LE
        
        # Greater than
        result = literal_10 > literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.GT
        
        # Greater than or equal
        result = literal_10 >= literal_20
        assert isinstance(result, BinaryOp)
        assert result.operator == OperatorType.GE
    
    def test_unary_operators(self, literal_10):
        """Test ExpressionNode unary operator overloading."""
        # Negation
        result = -literal_10
        assert isinstance(result, UnaryOp)
        assert result.operator == OperatorType.NEG
        
        # Positive
        result = +literal_10
        assert isinstance(result, UnaryOp)
        assert result.operator == OperatorType.POS


class TestFinancialCriticalScenarios:
    """Financial-critical edge cases."""
    
    def test_division_by_zero(self, literal_10):
        """Test division by zero handling."""
        zero_literal = Literal(0)
        op = BinaryOp(OperatorType.DIV, literal_10, zero_literal)
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            op.evaluate({})
    
    def test_modulo_by_zero(self, literal_10):
        """Test modulo by zero handling."""
        zero_literal = Literal(0)
        op = BinaryOp(OperatorType.MOD, literal_10, zero_literal)
        with pytest.raises(ZeroDivisionError, match="Cannot perform modulo with zero in series"):
            op.evaluate({})
    
    def test_power_with_large_exponent(self, literal_10):
        """Test power with large exponent."""
        large_literal = Literal(100)
        op = BinaryOp(OperatorType.POW, literal_10, large_literal)
        result = op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        # Should handle large numbers gracefully
    
    def test_complex_nested_expressions(self, literal_10, literal_20):
        """Test complex nested expressions."""
        # (10 + 20) * (10 - 20)
        add_op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        sub_op = BinaryOp(OperatorType.SUB, literal_10, literal_20)
        mul_op = BinaryOp(OperatorType.MUL, add_op, sub_op)
        
        result = mul_op.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(-300)  # (10 + 20) * (10 - 20) = 30 * (-10) = -300
    
    def test_dependency_tracking(self, literal_10, literal_20):
        """Test dependency tracking in complex expressions."""
        add_op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        mul_op = BinaryOp(OperatorType.MUL, add_op, literal_10)
        
        deps = mul_op.dependencies()
        assert isinstance(deps, list)
