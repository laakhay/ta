"""Expression node models for the computation graph."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Union
from enum import Enum
from datetime import datetime, timezone

from ..core import Series
from ..core.types import Price


class OperatorType(Enum):
    """Types of operators in expressions."""
    
    # Arithmetic
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    POW = "**"
    
    # Comparison
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    
    # Logical
    AND = "and"
    OR = "or"
    NOT = "not"
    
    # Unary
    NEG = "-"
    POS = "+"


@dataclass(eq=False)
class ExpressionNode(ABC):
    """Base class for expression nodes in the computation graph."""
    
    def __add__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Addition operator."""
        return BinaryOp(OperatorType.ADD, self, _wrap_literal(other))
    
    def __sub__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Subtraction operator."""
        return BinaryOp(OperatorType.SUB, self, _wrap_literal(other))
    
    def __mul__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Multiplication operator."""
        return BinaryOp(OperatorType.MUL, self, _wrap_literal(other))
    
    def __truediv__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Division operator."""
        return BinaryOp(OperatorType.DIV, self, _wrap_literal(other))
    
    def __mod__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Modulo operator."""
        return BinaryOp(OperatorType.MOD, self, _wrap_literal(other))
    
    def __pow__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Power operator."""
        return BinaryOp(OperatorType.POW, self, _wrap_literal(other))
    
    def __eq__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:  # type: ignore[override]
        """Equality operator."""
        return BinaryOp(OperatorType.EQ, self, _wrap_literal(other))
    
    def __ne__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:  # type: ignore[override]
        """Inequality operator."""
        return BinaryOp(OperatorType.NE, self, _wrap_literal(other))
    
    def __lt__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Less than operator."""
        return BinaryOp(OperatorType.LT, self, _wrap_literal(other))
    
    def __le__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Less than or equal operator."""
        return BinaryOp(OperatorType.LE, self, _wrap_literal(other))
    
    def __gt__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Greater than operator."""
        return BinaryOp(OperatorType.GT, self, _wrap_literal(other))
    
    def __ge__(self, other: Union[ExpressionNode, Series[Any], float, int]) -> BinaryOp:
        """Greater than or equal operator."""
        return BinaryOp(OperatorType.GE, self, _wrap_literal(other))
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((type(self).__name__, id(self)))
    
    def __neg__(self) -> UnaryOp:
        """Unary negation operator."""
        return UnaryOp(OperatorType.NEG, self)
    
    def __pos__(self) -> UnaryOp:
        """Unary plus operator."""
        return UnaryOp(OperatorType.POS, self)
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Series[Any]]) -> Series[Any]:
        """Evaluate the expression node given a context."""
        pass
    
    @abstractmethod
    def dependencies(self) -> List[str]:
        """Get list of dependencies (series names) this node requires."""
        pass
    
    @abstractmethod
    def describe(self) -> str:
        """Get a human-readable description of this node."""
        pass


@dataclass(eq=False)
class Literal(ExpressionNode):
    """Literal value node (constants, Series objects)."""
    
    value: Union[Series, float, int]
    
    def evaluate(self, context: Dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate literal value."""
        if isinstance(self.value, Series):
            return self.value
        
        # Convert scalar to Series with consistent timestamp
        # Use a fixed timestamp to ensure consistent evaluation
        # All literals use the same timestamp so they can be combined element-wise
        timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return Series[Any](
            timestamps=(timestamp,),
            values=(Price(self.value),),
            symbol="LITERAL",
            timeframe="1s"
        )
    
    def dependencies(self) -> List[str]:  # type: ignore[override]
        """Literal has no dependencies."""
        return []
    
    def describe(self) -> str:  # type: ignore[override]
        """Describe literal value."""
        if isinstance(self.value, Series):
            return f"Series({len(self.value)} points)"
        return str(self.value)
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((type(self).__name__, self.value))


@dataclass(eq=False)
class BinaryOp(ExpressionNode):
    """Binary operation node (e.g., a + b)."""
    
    operator: OperatorType
    left: ExpressionNode
    right: ExpressionNode
    
    def evaluate(self, context: Dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate binary operation."""
        left_result = self.left.evaluate(context)
        right_result = self.right.evaluate(context)
        
        # For element-wise operations, we need to handle different cases:
        # 1. Both Series have same length -> element-wise operation
        # 2. One Series has length 1 (scalar) -> broadcast to other Series length
        # 3. Different lengths -> error for now (could be enhanced with alignment)
        
        if len(left_result) != len(right_result):
            # Handle scalar broadcasting
            if len(left_result) == 1:
                # Left is scalar, broadcast to right
                left_result = Series(
                    timestamps=right_result.timestamps,
                    values=tuple(left_result.values[0] for _ in right_result.values),
                    symbol=left_result.symbol,
                    timeframe=left_result.timeframe
                )
            elif len(right_result) == 1:
                # Right is scalar, broadcast to left
                right_result = Series(
                    timestamps=left_result.timestamps,
                    values=tuple(right_result.values[0] for _ in left_result.values),
                    symbol=right_result.symbol,
                    timeframe=right_result.timeframe
                )
            else:
                raise ValueError(f"Cannot perform {self.operator.value} operation on series of different lengths: {len(left_result)} vs {len(right_result)}")
        
        # Perform element-wise operations
        if self.operator == OperatorType.ADD:
            return left_result + right_result
        elif self.operator == OperatorType.SUB:
            return left_result - right_result
        elif self.operator == OperatorType.MUL:
            return left_result * right_result
        elif self.operator == OperatorType.DIV:
            return left_result / right_result
        elif self.operator == OperatorType.MOD:
            return left_result % right_result
        elif self.operator == OperatorType.POW:
            return left_result ** right_result
        elif self.operator == OperatorType.EQ:
            # Comparison operators - for now, create a simple boolean series
            # In a full implementation, this would return boolean values
            timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            # Simple comparison - check if first values are equal
            result_value = 1 if left_result.values[0] == right_result.values[0] else 0
            return Series(
                timestamps=(timestamp,),
                values=(Price(result_value),),
                symbol="COMPARISON",
                timeframe="1s"
            )
        elif self.operator == OperatorType.NE:
            timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            result_value = 1 if left_result.values[0] != right_result.values[0] else 0
            return Series(
                timestamps=(timestamp,),
                values=(Price(result_value),),
                symbol="COMPARISON",
                timeframe="1s"
            )
        elif self.operator == OperatorType.LT:
            timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            result_value = 1 if left_result.values[0] < right_result.values[0] else 0
            return Series(
                timestamps=(timestamp,),
                values=(Price(result_value),),
                symbol="COMPARISON",
                timeframe="1s"
            )
        elif self.operator == OperatorType.LE:
            timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            result_value = 1 if left_result.values[0] <= right_result.values[0] else 0
            return Series(
                timestamps=(timestamp,),
                values=(Price(result_value),),
                symbol="COMPARISON",
                timeframe="1s"
            )
        elif self.operator == OperatorType.GT:
            timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            result_value = 1 if left_result.values[0] > right_result.values[0] else 0
            return Series(
                timestamps=(timestamp,),
                values=(Price(result_value),),
                symbol="COMPARISON",
                timeframe="1s"
            )
        elif self.operator == OperatorType.GE:
            timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            result_value = 1 if left_result.values[0] >= right_result.values[0] else 0
            return Series(
                timestamps=(timestamp,),
                values=(Price(result_value),),
                symbol="COMPARISON",
                timeframe="1s"
            )
        else:
            raise NotImplementedError(f"Binary operator {self.operator} not implemented")
    
    def dependencies(self) -> List[str]:  # type: ignore[override]
        """Get dependencies from both operands."""
        return list(set(self.left.dependencies() + self.right.dependencies()))
    
    def describe(self) -> str:  # type: ignore[override]
        """Describe binary operation."""
        return f"({self.left.describe()} {self.operator.value} {self.right.describe()})"
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((type(self).__name__, self.operator, self.left, self.right))


@dataclass(eq=False)
class UnaryOp(ExpressionNode):
    """Unary operation node (e.g., -a)."""
    
    operator: OperatorType
    operand: ExpressionNode
    
    def evaluate(self, context: Dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate unary operation."""
        operand_result = self.operand.evaluate(context)
        
        if self.operator == OperatorType.NEG:
            return -operand_result
        elif self.operator == OperatorType.POS:
            return operand_result
        else:
            raise NotImplementedError(f"Unary operator {self.operator} not implemented")
    
    def dependencies(self) -> List[str]:  # type: ignore[override]
        """Get dependencies from operand."""
        return self.operand.dependencies()
    
    def describe(self) -> str:  # type: ignore[override]
        """Describe unary operation."""
        return f"{self.operator.value}{self.operand.describe()}"
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((type(self).__name__, self.operator, self.operand))


def _wrap_literal(value: Union[ExpressionNode, Series[Any], float, int]) -> ExpressionNode:
    """Wrap a value in a Literal node if it's not already an ExpressionNode."""
    if isinstance(value, ExpressionNode):
        return value
    return Literal(value)
