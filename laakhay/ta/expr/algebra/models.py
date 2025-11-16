"""Expression node models for the computation graph."""

from __future__ import annotations

import operator as _py_operator
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any

from ...core import Series
from ...core.series import align_series
from ...core.types import Price


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


_OPERATOR_MAP = {
    _py_operator.add: OperatorType.ADD,
    _py_operator.sub: OperatorType.SUB,
    _py_operator.mul: OperatorType.MUL,
    _py_operator.truediv: OperatorType.DIV,
    _py_operator.mod: OperatorType.MOD,
    _py_operator.pow: OperatorType.POW,
    _py_operator.eq: OperatorType.EQ,
    _py_operator.ne: OperatorType.NE,
    _py_operator.lt: OperatorType.LT,
    _py_operator.le: OperatorType.LE,
    _py_operator.gt: OperatorType.GT,
    _py_operator.ge: OperatorType.GE,
    _py_operator.and_: OperatorType.AND,
    _py_operator.or_: OperatorType.OR,
    _py_operator.not_: OperatorType.NOT,
    _py_operator.neg: OperatorType.NEG,
    _py_operator.pos: OperatorType.POS,
}


def _resolve_operator(operator):
    if isinstance(operator, OperatorType):
        return operator
    elif operator in _OPERATOR_MAP:
        return _OPERATOR_MAP[operator]
    else:
        # Only report 'Binary operator' in message for test regex match
        raise NotImplementedError(f"Binary operator {operator} not implemented")


SCALAR_SYMBOL = "__SCALAR__"
SCALAR_TIMEFRAME = "1s"
SCALAR_TIMESTAMP = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)


def _coerce_decimal(value: Any) -> Price:
    """Coerce numeric literals into Decimals for price math."""
    if isinstance(value, Decimal):
        return Price(value)
    if isinstance(value, bool):
        return Price(Decimal(1 if value else 0))
    if isinstance(value, int | float | str):
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
    """Broadcast a scalar series to full metadata of the reference series."""
    if not _is_scalar_series(scalar):
        raise ValueError("Attempted to broadcast a non-scalar series")
    return Series[Any](
        timestamps=reference.timestamps,
        values=tuple(scalar.values[0] for _ in reference.timestamps),
        symbol=reference.symbol,
        timeframe=reference.timeframe,
    )


def _align_series(
    left: Series[Any] | Any,
    right: Series[Any] | Any,
    *,
    operator: OperatorType,
) -> tuple[Series[Any], Series[Any]]:
    if not isinstance(left, Series):
        left_series = _make_scalar_series(left)
        orig_left = None
    else:
        left_series = left
        orig_left = left

    if not isinstance(right, Series):
        right_series = _make_scalar_series(right)
        orig_right = None
    else:
        right_series = right
        orig_right = right

    left_scalar = _is_scalar_series(left_series)
    right_scalar = _is_scalar_series(right_series)
    # Broadcast scalars to match series meta (shape, symbol, timeframe)
    if left_scalar and not right_scalar:
        left_series = _broadcast_scalar_series(left_series, right_series)
    elif right_scalar and not left_scalar:
        right_series = _broadcast_scalar_series(right_series, left_series)
    # Ensure symbols/timeframes now match
    if left_series.symbol != right_series.symbol or left_series.timeframe != right_series.timeframe:
        raise ValueError("mismatched metadata")
    # Note: We allow series of different lengths - they will be aligned by timestamp
    # The align_series function handles this by matching timestamps
    how = "inner"
    fill = "none"
    try:
        aligned_left, aligned_right = align_series(
            left_series,
            right_series,
            how=how,
            fill=fill,
            left_fill_value=None,
            right_fill_value=None,
            symbol=left_series.symbol,
            timeframe=left_series.timeframe,
        )
        # align_series should always return series of the same length with how="inner"
        # If lengths don't match, it's a bug or the series have incompatible timestamps
        if len(aligned_left) != len(aligned_right):
            # Log for debugging - this shouldn't happen
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"align_series returned different lengths: left={len(aligned_left)}, right={len(aligned_right)}, "
                f"left_timestamps={len(aligned_left.timestamps) if aligned_left.timestamps else 0}, "
                f"right_timestamps={len(aligned_right.timestamps) if aligned_right.timestamps else 0}"
            )
            # Try to fix by re-aligning with the shorter length
            min_len = min(len(aligned_left), len(aligned_right))
            if min_len > 0:
                aligned_left = Series(
                    timestamps=aligned_left.timestamps[:min_len],
                    values=aligned_left.values[:min_len],
                    symbol=aligned_left.symbol,
                    timeframe=aligned_left.timeframe,
                )
                aligned_right = Series(
                    timestamps=aligned_right.timestamps[:min_len],
                    values=aligned_right.values[:min_len],
                    symbol=aligned_right.symbol,
                    timeframe=aligned_right.timeframe,
                )
            else:
                raise ValueError(f"Cannot perform {operator.value} on series of different lengths")
    except ValueError as ve:
        msg = str(ve)
        if "Alignment resulted in an empty timestamp set." in msg:
            raise ValueError(f"Cannot perform {operator.value} on series of different lengths")
        if "timestamp alignment" in msg:
            raise ValueError("timestamp alignment")
        raise
    # Preserve identity if unchanged
    if orig_left is not None and aligned_left == orig_left:
        aligned_left = orig_left
    if orig_right is not None and aligned_right == orig_right:
        aligned_right = orig_right
    return aligned_left, aligned_right


# Use new _align_series in _comparison_series
def _comparison_series(
    left: Series[Any],
    right: Series[Any],
    operator: OperatorType,
    compare: Callable[[Any, Any], bool],
) -> Series[bool]:
    # Ensure both operands are Series objects (convert scalars if needed)
    if not isinstance(left, Series):
        left = _make_scalar_series(left)
    if not isinstance(right, Series):
        right = _make_scalar_series(right)

    left_aligned, right_aligned = _align_series(left, right, operator=operator)
    result_values = tuple(
        bool(compare(lv, rv)) for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False)
    )
    return Series[bool](
        timestamps=left_aligned.timestamps,
        values=result_values,
        symbol=left_aligned.symbol,
        timeframe=left_aligned.timeframe,
    )


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
        op_type = _resolve_operator(self.operator)
        left_result = self.left.evaluate(context)
        right_result = self.right.evaluate(context)

        # Ensure both operands are Series objects (convert scalars if needed)
        if not isinstance(left_result, Series):
            left_result = _make_scalar_series(left_result)
        if not isinstance(right_result, Series):
            right_result = _make_scalar_series(right_result)

        result = None
        if op_type in {
            OperatorType.ADD,
            OperatorType.SUB,
            OperatorType.MUL,
            OperatorType.DIV,
            OperatorType.MOD,
            OperatorType.POW,
        }:
            try:
                left_aligned, right_aligned = _align_series(left_result, right_result, operator=op_type)
                if op_type == OperatorType.ADD:
                    result = left_aligned + right_aligned
                elif op_type == OperatorType.SUB:
                    result = left_aligned - right_aligned
                elif op_type == OperatorType.MUL:
                    result = left_aligned * right_aligned
                elif op_type == OperatorType.DIV:
                    result = left_aligned / right_aligned
                elif op_type == OperatorType.MOD:
                    result = left_aligned % right_aligned
                elif op_type == OperatorType.POW:
                    result = left_aligned**right_aligned
            except ValueError as ve:
                err = str(ve)
                if "mismatched metadata" in err or "symbol" in err or "timeframe" in err:
                    raise ValueError("mismatched metadata")
                elif "different lengths" in err or "empty timestamp" in err:
                    raise ValueError(f"Cannot perform {op_type.value} on series of different lengths")
                elif "timestamp alignment" in err:
                    raise ValueError("timestamp alignment")
                else:
                    raise
            except InvalidOperation as exc:
                raise ValueError("Invalid arithmetic operation in expression") from exc
        else:
            # All other ops as before
            if op_type == OperatorType.EQ:
                result = _comparison_series(left_result, right_result, op_type, lambda a, b: a == b)
            elif op_type == OperatorType.NE:
                result = _comparison_series(left_result, right_result, op_type, lambda a, b: a != b)
            elif op_type == OperatorType.LT:
                result = _comparison_series(left_result, right_result, op_type, lambda a, b: a < b)
            elif op_type == OperatorType.LE:
                result = _comparison_series(left_result, right_result, op_type, lambda a, b: a <= b)
            elif op_type == OperatorType.GT:
                result = _comparison_series(left_result, right_result, op_type, lambda a, b: a > b)
            elif op_type == OperatorType.GE:
                result = _comparison_series(left_result, right_result, op_type, lambda a, b: a >= b)
            elif op_type in {OperatorType.AND, OperatorType.OR}:
                left_aligned, right_aligned = _align_series(left_result, right_result, operator=op_type)

                def _truthy(v: Any) -> bool:
                    if isinstance(v, bool):
                        return v
                    if isinstance(v, int | float | Decimal):
                        return bool(Decimal(str(v)))
                    try:
                        return bool(Decimal(str(v)))
                    except Exception:
                        return bool(v)

                if op_type == OperatorType.AND:
                    values = tuple(
                        _truthy(lv) and _truthy(rv)
                        for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False)
                    )
                else:
                    values = tuple(
                        _truthy(lv) or _truthy(rv)
                        for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False)
                    )
                result = Series[bool](
                    timestamps=left_aligned.timestamps,
                    values=values,
                    symbol=left_aligned.symbol,
                    timeframe=left_aligned.timeframe,
                )
            else:
                raise NotImplementedError(f"Binary operator {self.operator} not implemented")
        return result

    def dependencies(self) -> list[str]:  # type: ignore[override]
        """Get dependencies from both operands."""
        return list(set(self.left.dependencies() + self.right.dependencies()))

    def describe(self) -> str:  # type: ignore[override]
        """Describe binary operation."""
        return f"({self.left.describe()} {self.operator.value} {self.right.describe()})"

    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((type(self).__name__, self.operator, self.left, self.right))

    def evaluate_aligned(self, left: Series[Any], right: Series[Any]) -> Series[Any]:
        op_type = _resolve_operator(self.operator)

        def _ensure_alignment() -> tuple[Series[Any], Series[Any]]:
            # Handle case where one operand might be a scalar (Decimal, int, float) instead of a Series
            # This can happen when the library receives raw numeric values during evaluation
            # Convert scalars to Series objects before alignment
            if not isinstance(left, Series):
                left_series = _make_scalar_series(left)
            else:
                left_series = left

            if not isinstance(right, Series):
                right_series = _make_scalar_series(right)
            else:
                right_series = right

            aligned_meta = (
                left_series.symbol == right_series.symbol
                and left_series.timeframe == right_series.timeframe
                and left_series.timestamps == right_series.timestamps
                and len(left_series.values) == len(right_series.values)
            )
            if aligned_meta:
                return left_series, right_series
            return _align_series(left_series, right_series, operator=op_type)

        left_aligned, right_aligned = _ensure_alignment()

        if op_type == OperatorType.ADD:
            return left_aligned + right_aligned
        if op_type == OperatorType.SUB:
            return left_aligned - right_aligned
        if op_type == OperatorType.MUL:
            return left_aligned * right_aligned
        if op_type == OperatorType.DIV:
            return left_aligned / right_aligned
        if op_type == OperatorType.MOD:
            return left_aligned % right_aligned
        if op_type == OperatorType.POW:
            return left_aligned**right_aligned
        if op_type == OperatorType.EQ:
            return _comparison_series(left_aligned, right_aligned, op_type, lambda a, b: a == b)
        if op_type == OperatorType.NE:
            return _comparison_series(left_aligned, right_aligned, op_type, lambda a, b: a != b)
        if op_type == OperatorType.LT:
            return _comparison_series(left_aligned, right_aligned, op_type, lambda a, b: a < b)
        if op_type == OperatorType.LE:
            return _comparison_series(left_aligned, right_aligned, op_type, lambda a, b: a <= b)
        if op_type == OperatorType.GT:
            return _comparison_series(left_aligned, right_aligned, op_type, lambda a, b: a > b)
        if op_type == OperatorType.GE:
            return _comparison_series(left_aligned, right_aligned, op_type, lambda a, b: a >= b)
        if op_type in {OperatorType.AND, OperatorType.OR}:

            def _truthy(value: Any) -> bool:
                if isinstance(value, bool):
                    return value
                if isinstance(value, int | float | Decimal):
                    return bool(Decimal(str(value)))
                try:
                    return bool(Decimal(str(value)))
                except Exception:
                    return bool(value)

            values = tuple(
                _truthy(lv) and _truthy(rv) if op_type == OperatorType.AND else _truthy(lv) or _truthy(rv)
                for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False)
            )
            return Series[bool](
                timestamps=left_aligned.timestamps,
                values=values,
                symbol=left_aligned.symbol,
                timeframe=left_aligned.timeframe,
            )
        raise NotImplementedError(f"operator {self.operator} not supported in evaluate_aligned")


@dataclass(eq=False)
class UnaryOp(ExpressionNode):
    """Unary operation node (e.g., -a)."""

    operator: OperatorType
    operand: ExpressionNode

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        op_type = _resolve_operator(self.operator)
        operand_result = self.operand.evaluate(context)
        if op_type == OperatorType.NEG:
            result = -operand_result
        elif op_type == OperatorType.POS:
            result = operand_result
        elif op_type == OperatorType.NOT:

            def _truthy(v: Any) -> bool:
                if isinstance(v, bool):
                    return v
                if isinstance(v, int | float | Decimal):
                    return bool(Decimal(str(v)))
                try:
                    return bool(Decimal(str(v)))
                except Exception:
                    return bool(v)

            result = Series[bool](
                timestamps=operand_result.timestamps,
                values=tuple(not _truthy(v) for v in operand_result.values),
                symbol=operand_result.symbol,
                timeframe=operand_result.timeframe,
            )
        else:
            raise NotImplementedError(f"Unary operator {self.operator} not implemented")
        return result

    def dependencies(self) -> list[str]:  # type: ignore[override]
        """Get dependencies from operand."""
        return self.operand.dependencies()

    def describe(self) -> str:  # type: ignore[override]
        """Describe unary operation."""
        return f"{self.operator.value}{self.operand.describe()}"

    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((type(self).__name__, self.operator, self.operand))


@dataclass(eq=False)
class SourceExpression(ExpressionNode):
    """Expression that references a data source field."""

    symbol: str
    field: str  # 'price', 'volume', 'count', 'imbalance', etc.
    exchange: str | None = None
    timeframe: str | None = None
    source: str = "ohlcv"  # 'ohlcv', 'trades', 'orderbook', 'liquidation'
    base: str | None = None  # BTC (from BTC/USDT)
    quote: str | None = None  # USDT (from BTC/USDT)
    instrument_type: str | None = None  # spot, perp, perpetual, futures, future, option

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate source expression - resolved at evaluation time."""
        # This will be implemented in the evaluator
        raise NotImplementedError("SourceExpression evaluation is handled by the evaluator")

    def dependencies(self) -> list[str]:  # type: ignore[override]
        """Get dependencies for source expression."""
        key_parts = [self.source, self.symbol]
        if self.timeframe:
            key_parts.append(self.timeframe)
        if self.exchange:
            key_parts.append(self.exchange)
        key_parts.append(self.field)
        return [".".join(key_parts)]

    def describe(self) -> str:  # type: ignore[override]
        """Describe source expression."""
        parts = []
        if self.exchange:
            parts.append(self.exchange)
        parts.append(self.symbol)
        if self.instrument_type:
            parts.append(self.instrument_type)
        if self.timeframe:
            parts.append(self.timeframe)
        parts.append(self.source)
        parts.append(self.field)
        return ".".join(parts)


@dataclass(eq=False)
class FilterExpression(ExpressionNode):
    """Expression that filters a series."""

    series: ExpressionNode
    condition: ExpressionNode

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate filter expression - implemented in evaluator."""
        raise NotImplementedError("FilterExpression evaluation is handled by the evaluator")

    def dependencies(self) -> list[str]:  # type: ignore[override]
        """Get dependencies from series and condition."""
        return list(set(self.series.dependencies() + self.condition.dependencies()))

    def describe(self) -> str:  # type: ignore[override]
        """Describe filter expression."""
        return f"{self.series.describe()}.filter({self.condition.describe()})"


@dataclass(eq=False)
class AggregateExpression(ExpressionNode):
    """Expression that aggregates a series."""

    series: ExpressionNode
    operation: str  # 'count', 'sum', 'avg', 'max', 'min'
    field: str | None

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate aggregate expression - implemented in evaluator."""
        raise NotImplementedError("AggregateExpression evaluation is handled by the evaluator")

    def dependencies(self) -> list[str]:  # type: ignore[override]
        """Get dependencies from series."""
        return self.series.dependencies()

    def describe(self) -> str:  # type: ignore[override]
        """Describe aggregate expression."""
        if self.field:
            return f"{self.series.describe()}.{self.operation}({self.field})"
        return f"{self.series.describe()}.{self.operation}"


@dataclass(eq=False)
class TimeShiftExpression(ExpressionNode):
    """Expression that queries historical data."""

    series: ExpressionNode
    shift: str  # '24h_ago', '1h', etc.
    operation: str | None  # 'change', 'change_pct', 'spike', etc.

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:  # type: ignore[override]
        """Evaluate time-shift expression - implemented in evaluator."""
        raise NotImplementedError("TimeShiftExpression evaluation is handled by the evaluator")

    def dependencies(self) -> list[str]:  # type: ignore[override]
        """Get dependencies from series."""
        return self.series.dependencies()

    def describe(self) -> str:  # type: ignore[override]
        """Describe time-shift expression."""
        if self.operation:
            return f"{self.series.describe()}.{self.operation}_{self.shift}"
        return f"{self.series.describe()}.{self.shift}"


def _wrap_literal(value: ExpressionNode | Series[Any] | float | int) -> ExpressionNode:
    """Wrap a value in a Literal node if it's not already an ExpressionNode."""
    if isinstance(value, ExpressionNode):
        return value
    return Literal(value)
