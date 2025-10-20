"""Consolidated expressions operators tests - lean and efficient."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.expressions.operators import Expression, as_expression
from laakhay.ta.expressions.models import Literal, BinaryOp, UnaryOp, OperatorType
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price


class TestExpression:
    """Expression wrapper class tests."""
    
    def test_creation_from_literal(self, literal_10):
        """Test Expression creation from literal."""
        expr = Expression(literal_10)
        assert expr._node == literal_10
    
    def test_creation_from_series(self, test_series):
        """Test Expression creation from series."""
        expr = Expression(test_series)
        assert isinstance(expr._node, (Literal, Series))
        if isinstance(expr._node, Literal):
            assert expr._node.value == test_series
    
    def test_creation_from_scalar(self):
        """Test Expression creation from scalar."""
        expr = Expression(42)
        assert isinstance(expr._node, (Literal, int))
        if isinstance(expr._node, Literal):
            assert expr._node.value == 42
    
    def test_evaluate(self, literal_10):
        """Test Expression evaluation."""
        expr = Expression(literal_10)
        context = {}
        result = expr.evaluate(context)
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(10)
    
    def test_dependencies(self, literal_10, literal_20):
        """Test Expression dependencies."""
        add_op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        expr = Expression(add_op)
        deps = expr.dependencies()
        assert isinstance(deps, list)
    
    def test_describe(self, literal_10, literal_20):
        """Test Expression description."""
        add_op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        expr = Expression(add_op)
        desc = expr.describe()
        assert desc == "(10 + 20)"
    
    def test_arithmetic_operators(self, literal_10, literal_20):
        """Test Expression arithmetic operator overloading."""
        expr1 = Expression(literal_10)
        expr2 = Expression(literal_20)
        
        # Addition
        result = expr1 + expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.ADD
        
        # Subtraction
        result = expr1 - expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.SUB
        
        # Multiplication
        result = expr1 * expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.MUL
        
        # Division
        result = expr1 / expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.DIV
        
        # Modulo
        result = expr1 % expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.MOD
        
        # Power
        result = expr1 ** expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.POW
    
    def test_comparison_operators(self, literal_10, literal_20):
        """Test Expression comparison operator overloading."""
        expr1 = Expression(literal_10)
        expr2 = Expression(literal_20)
        
        # Equality
        result = expr1 == expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.EQ
        
        # Inequality
        result = expr1 != expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.NE
        
        # Less than
        result = expr1 < expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.LT
        
        # Less than or equal
        result = expr1 <= expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.LE
        
        # Greater than
        result = expr1 > expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.GT
        
        # Greater than or equal
        result = expr1 >= expr2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.GE
    
    def test_unary_operators(self, literal_10):
        """Test Expression unary operator overloading."""
        expr = Expression(literal_10)
        
        # Negation
        result = -expr
        assert isinstance(result, Expression)
        assert isinstance(result._node, UnaryOp)
        assert result._node.operator == OperatorType.NEG
        
        # Positive
        result = +expr
        assert isinstance(result, Expression)
        assert isinstance(result._node, UnaryOp)
        assert result._node.operator == OperatorType.POS
    
    def test_scalar_operations(self, literal_10):
        """Test Expression operations with scalars."""
        expr = Expression(literal_10)
        
        # Addition with scalar
        result = expr + 5
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.ADD
        
        # Subtraction with scalar
        result = expr - 5
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.SUB
        
        # Multiplication with scalar
        result = expr * 5
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.MUL
        
        # Division with scalar
        result = expr / 5
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.DIV
        
        # Modulo with scalar
        result = expr % 5
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.MOD
        
        # Power with scalar
        result = expr ** 2
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.POW
    
    def test_expression_chaining(self, literal_10, literal_20):
        """Test Expression chaining."""
        expr1 = Expression(literal_10)
        expr2 = Expression(literal_20)
        
        # Chain: (10 + 20) * 10
        add_expr = expr1 + expr2
        mul_expr = add_expr * expr1
        
        assert isinstance(mul_expr, Expression)
        assert isinstance(mul_expr._node, BinaryOp)
        assert mul_expr._node.operator == OperatorType.MUL
        
        # Evaluate the chained expression
        result = mul_expr.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(300)  # (10 + 20) * 10 = 300


class TestAsExpression:
    """as_expression function tests."""
    
    def test_as_expression_scalar(self):
        """Test as_expression with scalar."""
        expr = as_expression(42)
        assert isinstance(expr, Expression)
        assert isinstance(expr._node, Literal)
        assert expr._node.value == 42
    
    def test_as_expression_series(self, test_series):
        """Test as_expression with series."""
        expr = as_expression(test_series)
        assert isinstance(expr, Expression)
        assert isinstance(expr._node, Literal)
        assert expr._node.value == test_series
    
    def test_as_expression_literal(self, literal_10):
        """Test as_expression with literal."""
        expr = as_expression(literal_10)
        assert isinstance(expr, Expression)
        assert expr._node == literal_10
    
    def test_as_expression_binary_op(self, literal_10, literal_20):
        """Test as_expression with binary operation."""
        add_op = BinaryOp(OperatorType.ADD, literal_10, literal_20)
        expr = as_expression(add_op)
        assert isinstance(expr, Expression)
        assert expr._node == add_op
    
    def test_as_expression_already_expression(self, literal_10):
        """Test as_expression with already wrapped expression."""
        original_expr = Expression(literal_10)
        expr = as_expression(original_expr)
        assert expr == original_expr
    
    def test_as_expression_operator_chaining(self, literal_10, literal_20):
        """Test as_expression with operator chaining."""
        # Test: as_expression(10) + as_expression(20)
        expr1 = as_expression(literal_10)
        expr2 = as_expression(literal_20)
        result = expr1 + expr2
        
        assert isinstance(result, Expression)
        assert isinstance(result._node, BinaryOp)
        assert result._node.operator == OperatorType.ADD
        assert result._node.left == literal_10
        assert result._node.right == literal_20


class TestExpressionHelpers:
    """Expression helper function tests."""
    
    def test_expression_creation_helpers(self):
        """Test Expression creation with various inputs."""
        # Test scalar
        expr1 = Expression(42)
        assert expr1 is not None
        
        # Test string
        expr2 = Expression("test")
        assert expr2 is not None
        
        # Test list
        expr3 = Expression([1, 2, 3])
        assert expr3 is not None


class TestExpressionEvaluationEdgeCases:
    """Expression evaluation edge cases."""
    
    def test_empty_context(self, literal_10):
        """Test Expression evaluation with empty context."""
        expr = Expression(literal_10)
        result = expr.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(10)
    
    def test_none_context(self, literal_10):
        """Test Expression evaluation with None context."""
        expr = Expression(literal_10)
        result = expr.evaluate(None)
        assert isinstance(result, Series)
        assert len(result) == 1
        assert result.values[0] == Price(10)
    
    def test_complex_nested_evaluation(self, literal_10, literal_20):
        """Test complex nested expression evaluation."""
        # ((10 + 20) * 10) - (20 / 10)
        add_expr = Expression(literal_10) + Expression(literal_20)
        mul_expr = add_expr * Expression(literal_10)
        div_expr = Expression(literal_20) / Expression(literal_10)
        final_expr = mul_expr - div_expr
        
        result = final_expr.evaluate({})
        assert isinstance(result, Series)
        assert len(result) == 1
        # ((10 + 20) * 10) - (20 / 10) = (30 * 10) - 2 = 300 - 2 = 298
        assert result.values[0] == Price(298)
    
    def test_dependency_tracking_complex(self, literal_10, literal_20):
        """Test dependency tracking in complex expressions."""
        expr1 = Expression(literal_10)
        expr2 = Expression(literal_20)
        
        # (10 + 20) * (10 - 20)
        add_expr = expr1 + expr2
        sub_expr = expr1 - expr2
        mul_expr = add_expr * sub_expr
        
        deps = mul_expr.dependencies()
        assert isinstance(deps, list)


class TestFinancialCriticalScenarios:
    """Financial-critical scenarios for Expression."""
    
    def test_price_calculation_precision(self):
        """Test price calculation with high precision."""
        price1 = Decimal("100.123456789")
        price2 = Decimal("200.987654321")
        
        expr1 = Expression(Literal(price1))
        expr2 = Expression(Literal(price2))
        result = expr1 + expr2
        
        eval_result = result.evaluate({})
        assert isinstance(eval_result, Series)
        assert len(eval_result) == 1
        expected = price1 + price2
        assert eval_result.values[0] == Price(expected)
    
    def test_division_by_very_small_number(self):
        """Test division by very small number."""
        large_num = Decimal("1000000000000")
        small_num = Decimal("0.0000000001")
        
        expr1 = Expression(Literal(large_num))
        expr2 = Expression(Literal(small_num))
        result = expr1 / expr2
        
        eval_result = result.evaluate({})
        assert isinstance(eval_result, Series)
        assert len(eval_result) == 1
        # Should handle very large results
        assert eval_result.values[0] > Price(Decimal("1000000000000"))
    
    def test_modulo_with_large_numbers(self):
        """Test modulo with large numbers."""
        large_num = Decimal("1000000000000")
        mod_num = Decimal("7")
        
        expr1 = Expression(Literal(large_num))
        expr2 = Expression(Literal(mod_num))
        result = expr1 % expr2
        
        eval_result = result.evaluate({})
        assert isinstance(eval_result, Series)
        assert len(eval_result) == 1
        expected = large_num % mod_num
        assert eval_result.values[0] == Price(expected)
    
    def test_power_with_fractional_exponent(self):
        """Test power with fractional exponent."""
        base = Decimal("100")
        exponent = Decimal("0.5")  # Square root
        
        expr1 = Expression(Literal(base))
        expr2 = Expression(Literal(exponent))
        result = expr1 ** expr2
        
        eval_result = result.evaluate({})
        assert isinstance(eval_result, Series)
        assert len(eval_result) == 1
        # Should handle fractional powers
        assert eval_result.values[0] > Price(Decimal("9"))  # sqrt(100) = 10
    
    def test_mixed_decimal_float_comparisons(self):
        """Test mixed decimal and float comparisons."""
        decimal_val = Decimal("100.5")
        float_val = 100.5
        
        expr1 = Expression(Literal(decimal_val))
        expr2 = Expression(Literal(float_val))
        result = expr1 == expr2
        
        eval_result = result.evaluate({})
        assert isinstance(eval_result, Series)
        assert len(eval_result) == 1
        # Should handle mixed type comparisons
        assert eval_result.values[0] == Price(1)  # True
