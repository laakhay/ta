"""Expression node models for the computation graph."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any

from ..core import Series
from ..core.series import align_series
from .alignment import get_policy
from ..core.types import Price

SCALAR_SYMBOL = "__SCALAR__"
SCALAR_TIMEFRAME = "1s"
SCALAR_TIMESTAMP = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)


def _coerce_decimal(value: Any) -> Price:
    """Coerce numeric literals into Decimals for price math."""
    if isinstance(value, Decimal):
        return Price(value)
    if isinstance(value, bool):
        return Price(Decimal(1 if value else 0))
    if isinstance(value, (int, float, str)):
        try:
            return Price(Decimal(str(value)))
        except InvalidOperation as exc:  # pragma: no cover - defensive
            raise TypeError(f"Unsupported scalar literal {value!r}") from exc
    raise TypeError(f"Unsupported scalar literal type: {type(value).__name__}")


def _make_scalar_series(value: Any) -> Series[Price]:
    """Create a single-point series representing a scalar literal."""
    coerced = _coerce_decimal(value)
    return Series[Price](
        timestamps=(SCALAR_TIMESTAMP,),
        values=(coerced,),
        symbol=SCALAR_SYMBOL,
        timeframe=SCALAR_TIMEFRAME,
    )


def _is_scalar_series(series: Series[Any]) -> bool:
    """True if the series represents a scalar literal."""
    return series.symbol == SCALAR_SYMBOL


def _broadcast_scalar_series(scalar: Series[Any], reference: Series[Any]) -> Series[Any]:
    """Broadcast a scalar series to match the metadata of a reference series."""
    if not _is_scalar_series(scalar):
        raise ValueError("Attempted to broadcast a non-scalar series")
    repeated_values = tuple(scalar.values[0] for _ in reference.timestamps)
    return Series[Any](
        timestamps=reference.timestamps,
        values=repeated_values,
        symbol=reference.symbol,
        timeframe=reference.timeframe,
    )


def _align_series(
    left: Series[Any],
    right: Series[Any],
    *,
    operator: OperatorType,
) -> tuple[Series[Any], Series[Any]]:
    """Align two series for arithmetic/comparison operations using policy defaults."""
    if _is_scalar_series(left) and not _is_scalar_series(right):
        left = _broadcast_scalar_series(left, right)
    if _is_scalar_series(right) and not _is_scalar_series(left):
        right = _broadcast_scalar_series(right, left)

    how, fill, lfv, rfv = get_policy()
    return align_series(left, right, how=how, fill=fill, left_fill_value=lfv, right_fill_value=rfv)


def _comparison_series(
    left: Series[Any],
    right: Series[Any],
    operator: OperatorType,
    compare: Callable[[Any, Any], bool],
) -> Series[bool]:
    """Produce a boolean series from comparing two aligned series."""
    left_aligned, right_aligned = _align_series(left, right, operator=operator)
    result_values = tuple(compare(lv, rv) for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False))
    return Series[bool](
        timestamps=left_aligned.timestamps,
        values=result_values,
        symbol=left_aligned.symbol,
        timeframe=left_aligned.timeframe,
    )


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

    def __add__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Addition operator."""
        return BinaryOp(OperatorType.ADD, self, _wrap_literal(other))

    def __sub__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Subtraction operator."""
        return BinaryOp(OperatorType.SUB, self, _wrap_literal(other))

    def __mul__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Multiplication operator."""
        return BinaryOp(OperatorType.MUL, self, _wrap_literal(other))

    def __truediv__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Division operator."""
        return BinaryOp(OperatorType.DIV, self, _wrap_literal(other))

    def __mod__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Modulo operator."""
        return BinaryOp(OperatorType.MOD, self, _wrap_literal(other))

    def __pow__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Power operator."""
        return BinaryOp(OperatorType.POW, self, _wrap_literal(other))

    def __eq__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:  # type: ignore[override]
        """Equality operator."""
        return BinaryOp(OperatorType.EQ, self, _wrap_literal(other))

    def __ne__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:  # type: ignore[override]
        """Inequality operator."""
        return BinaryOp(OperatorType.NE, self, _wrap_literal(other))

    def __lt__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Less than operator."""
        return BinaryOp(OperatorType.LT, self, _wrap_literal(other))

    def __le__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Less than or equal operator."""
        return BinaryOp(OperatorType.LE, self, _wrap_literal(other))

    def __gt__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Greater than operator."""
        return BinaryOp(OperatorType.GT, self, _wrap_literal(other))

    def __ge__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Greater than or equal operator."""
        return BinaryOp(OperatorType.GE, self, _wrap_literal(other))

    # Logical bitwise overloads to represent boolean logic in expressions
    def __and__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Logical AND (element-wise) using bitwise '&'."""
        return BinaryOp(OperatorType.AND, self, _wrap_literal(other))

    def __or__(self, other: ExpressionNode | Series[Any] | float | int) -> BinaryOp:
        """Logical OR (element-wise) using bitwise '|'."""
        return BinaryOp(OperatorType.OR, self, _wrap_literal(other))

    def __invert__(self) -> UnaryOp:
        """Logical NOT (element-wise) using bitwise '~'."""
        return UnaryOp(OperatorType.NOT, self)

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
    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        """Evaluate the expression node given a context."""
        pass

    @abstractmethod
    def dependencies(self) -> list[str]:
        """Get list of dependencies (series names) this node requires."""
        pass

    @abstractmethod
    def describe(self) -> str:
        """Get a human-readable description of this node."""
        pass


@dataclass(eq=False)
class Literal(ExpressionNode):
    """Literal value node (constants, Series objects)."""

    value: Series | float | int

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate literal value."""
        if isinstance(self.value, Series):
            return self.value
        return _make_scalar_series(self.value)

    def dependencies(self) -> list[str]:  # type: ignore[override]
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

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate binary operation."""
        left_result = self.left.evaluate(context)
        right_result = self.right.evaluate(context)

        if self.operator in {
            OperatorType.ADD,
            OperatorType.SUB,
            OperatorType.MUL,
            OperatorType.DIV,
            OperatorType.MOD,
            OperatorType.POW,
        }:
            left_aligned, right_aligned = _align_series(left_result, right_result, operator=self.operator)
            try:
                if self.operator == OperatorType.ADD:
                    return left_aligned + right_aligned
                if self.operator == OperatorType.SUB:
                    return left_aligned - right_aligned
                if self.operator == OperatorType.MUL:
                    return left_aligned * right_aligned
                if self.operator == OperatorType.DIV:
                    return left_aligned / right_aligned
                if self.operator == OperatorType.MOD:
                    return left_aligned % right_aligned
                if self.operator == OperatorType.POW:
                    return left_aligned ** right_aligned
            except ValueError:
                raise
            except InvalidOperation as exc:
                raise ValueError("Invalid arithmetic operation in expression") from exc

        if self.operator == OperatorType.EQ:
            return _comparison_series(left_result, right_result, self.operator, lambda a, b: a == b)
        if self.operator == OperatorType.NE:
            return _comparison_series(left_result, right_result, self.operator, lambda a, b: a != b)
        if self.operator == OperatorType.LT:
            return _comparison_series(left_result, right_result, self.operator, lambda a, b: a < b)
        if self.operator == OperatorType.LE:
            return _comparison_series(left_result, right_result, self.operator, lambda a, b: a <= b)
        if self.operator == OperatorType.GT:
            return _comparison_series(left_result, right_result, self.operator, lambda a, b: a > b)
        if self.operator == OperatorType.GE:
            return _comparison_series(left_result, right_result, self.operator, lambda a, b: a >= b)

        # Logical operations: element-wise boolean logic on aligned series
        if self.operator in {OperatorType.AND, OperatorType.OR}:
            left_aligned, right_aligned = _align_series(left_result, right_result, operator=self.operator)

            def _truthy(v: Any) -> bool:
                if isinstance(v, bool):
                    return v
                if isinstance(v, (int, float, Decimal)):
                    return bool(Decimal(str(v)))
                try:
                    return bool(Decimal(str(v)))
                except Exception:
                    return bool(v)

            if self.operator == OperatorType.AND:
                values = tuple(_truthy(lv) and _truthy(rv) for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False))
            else:
                values = tuple(_truthy(lv) or _truthy(rv) for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False))

            return Series[bool](
                timestamps=left_aligned.timestamps,
                values=values,
                symbol=left_aligned.symbol,
                timeframe=left_aligned.timeframe,
            )

        raise NotImplementedError(f"Binary operator {self.operator} not implemented")

    def dependencies(self) -> list[str]:  # type: ignore[override]
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

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate unary operation."""
        operand_result = self.operand.evaluate(context)

        if self.operator == OperatorType.NEG:
            return -operand_result
        elif self.operator == OperatorType.POS:
            return operand_result
        elif self.operator == OperatorType.NOT:
            def _truthy(v: Any) -> bool:
                if isinstance(v, bool):
                    return v
                if isinstance(v, (int, float, Decimal)):
                    return bool(Decimal(str(v)))
                try:
                    return bool(Decimal(str(v)))
                except Exception:
                    return bool(v)

            return Series[bool](
                timestamps=operand_result.timestamps,
                values=tuple(not _truthy(v) for v in operand_result.values),
                symbol=operand_result.symbol,
                timeframe=operand_result.timeframe,
            )
        else:
            raise NotImplementedError(f"Unary operator {self.operator} not implemented")

    def dependencies(self) -> list[str]:  # type: ignore[override]
        """Get dependencies from operand."""
        return self.operand.dependencies()

    def describe(self) -> str:  # type: ignore[override]
        """Describe unary operation."""
        return f"{self.operator.value}{self.operand.describe()}"

    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((type(self).__name__, self.operator, self.operand))


def _wrap_literal(value: ExpressionNode | Series[Any] | float | int) -> ExpressionNode:
    """Wrap a value in a Literal node if it's not already an ExpressionNode."""
    if isinstance(value, ExpressionNode):
        return value
    return Literal(value)
