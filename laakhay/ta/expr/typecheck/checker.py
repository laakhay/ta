"""Type checking of strategy expression IR."""

from typing import Any

from ...registry.registry import get_global_registry
from ..ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    CanonicalExpression,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
)
from ..semantics.source_schema import is_valid_source_field


class TypeCheckError(ValueError):
    """Raised when an expression fails static type checking."""

    pass


def typecheck_expression(expr: CanonicalExpression) -> CanonicalExpression:
    """Verify semantic correctness and type safety of an expression."""
    if isinstance(expr, LiteralNode):
        return expr

    if isinstance(expr, SourceRefNode):
        return expr

    if isinstance(expr, UnaryOpNode):
        typecheck_expression(expr.operand)
        return expr

    if isinstance(expr, BinaryOpNode):
        typecheck_expression(expr.left)
        typecheck_expression(expr.right)
        return expr

    if isinstance(expr, CallNode):
        _typecheck_call(expr)
        for arg in expr.args:
            typecheck_expression(arg)
        for kwarg in expr.kwargs.values():
            typecheck_expression(kwarg)
        return expr

    if isinstance(expr, FilterNode):
        _typecheck_filter(expr)
        typecheck_expression(expr.series)
        typecheck_expression(expr.condition)
        return expr

    if isinstance(expr, AggregateNode):
        _typecheck_aggregate(expr)
        typecheck_expression(expr.series)
        return expr

    if isinstance(expr, TimeShiftNode):
        _typecheck_timeshift(expr)
        typecheck_expression(expr.series)
        return expr

    return expr


def _typecheck_call(node: CallNode) -> None:
    """Validate a CallNode against its indicator schema."""
    registry = get_global_registry()
    handle = registry.get(node.name)

    if handle is None:
        raise TypeCheckError(f"Unknown indicator: {node.name}")

    schema = handle.schema
    params = list(schema.parameters.values())

    # Map positional args to params
    assigned_params: set[str] = set()

    # DSL/Parser Heuristic: The first argument in the IR might be the "primary series"
    # which binds to the SeriesContext rather than a Python parameter.
    # We skip the first arg if:
    # 1. It is not a LiteralNode (it's an expression/series)
    # 2. AND (The indicator has no params OR the first param is NOT a Series)
    # This prevents mapping sma(close, 20) -> close:period, 20:source.
    from ...core.series import Series

    effective_args = list(node.args)
    if effective_args:
        first_arg = effective_args[0]
        first_param = params[0] if params else None

        is_implicit_series = not isinstance(first_arg, LiteralNode) and (
            first_param is None or first_param.type is not Series
        )

        if is_implicit_series:
            effective_args.pop(0)

    if len(effective_args) > len(params):
        raise TypeCheckError(
            f"[{node.name}] Too many positional arguments: expected at most {len(params)}, got {len(effective_args)}"
        )

    for i, arg in enumerate(effective_args):
        param = params[i]
        _validate_param_value(node.name, param.name, arg, param.type)
        assigned_params.add(param.name)

    # Validate keyword args
    for name, value in node.kwargs.items():
        if name not in schema.parameters:
            raise TypeCheckError(f"[{node.name}] Unknown keyword argument: {name}")

        if name in assigned_params:
            raise TypeCheckError(f"[{node.name}] Parameter '{name}' specified both positionally and as keyword")

        param = schema.parameters[name]
        _validate_param_value(node.name, name, value, param.type)
        assigned_params.add(name)

    # Check for missing required parameters
    for name, param in schema.parameters.items():
        if param.required and name not in assigned_params:
            raise TypeCheckError(f"[{node.name}] Missing required parameter: {name}")


def _validate_param_value(indicator_name: str, param_name: str, value: Any, expected_type: type) -> None:
    """Validate a parameter value against its expected type."""
    from ...core.series import Series

    actual_node = value
    is_literal = isinstance(actual_node, LiteralNode)

    # If it's a Series type in schema, it must be an expression, not a bare literal
    # (unless the literal is somehow a Series, which it shouldn't be in the DSL)
    if expected_type is Series:
        if is_literal:
            raise TypeCheckError(
                f"[{indicator_name}] Parameter '{param_name}' expects a Series (expression), got literal {type(actual_node.value).__name__}"
            )
        return

    # If it's a scalar type, it MUST be a LiteralNode
    if expected_type in (int, float, str, bool):
        if not is_literal:
            raise TypeCheckError(
                f"[{indicator_name}] Parameter '{param_name}' expects a scalar {expected_type.__name__}, got {type(actual_node).__name__}"
            )

        val = actual_node.value
        if not isinstance(val, expected_type):
            # Safe coercion: int -> float or float(whole) -> int
            if expected_type is float and isinstance(val, int):
                pass
            elif expected_type is int and isinstance(val, float) and val.is_integer():
                pass
            else:
                raise TypeCheckError(
                    f"[{indicator_name}] Parameter '{param_name}' expects {expected_type.__name__}, got {type(val).__name__}"
                )

        # Value validation: Periods must be positive
        if param_name.lower() in ("period", "lookback", "fast_period", "slow_period", "signal_period"):
            if isinstance(val, int | float) and val <= 0:
                raise TypeCheckError(f"[{indicator_name}] Parameter '{param_name}' must be positive, got {val}")


def _typecheck_filter(node: FilterNode) -> None:
    """Validate a FilterNode."""
    # Condition should generally be a comparison or logical op
    if isinstance(node.condition, LiteralNode):
        if not isinstance(node.condition.value, bool):
            raise TypeCheckError(
                f"[filter] Condition must be boolean, got literal {type(node.condition.value).__name__}"
            )

    if isinstance(node.condition, BinaryOpNode):
        comparison_ops = {"gt", "gte", "lt", "lte", "eq", "neq", "and", "or"}
        if node.condition.operator not in comparison_ops:
            raise TypeCheckError(
                f"[filter] Condition uses non-boolean operator '{node.condition.operator}'. "
                "Expected comparison or logical operator."
            )


def _typecheck_aggregate(node: AggregateNode) -> None:
    """Validate an AggregateNode."""
    if not node.operation:
        raise TypeCheckError("[aggregate] Missing operation")

    valid_ops = {"sum", "avg", "max", "min", "count"}
    if node.operation.lower() not in valid_ops:
        raise TypeCheckError(f"[aggregate] Unknown operation: {node.operation}")

    if node.field is not None and not node.field:
        raise TypeCheckError("[aggregate] Field name cannot be empty")

    # If series is a SourceRefNode, we can validate the field
    if isinstance(node.series, SourceRefNode):
        source = node.series.source.lower()
        field = node.field or node.series.field
        _validate_source_field(source, field)


def _typecheck_timeshift(node: TimeShiftNode) -> None:
    """Validate a TimeShiftNode."""
    import re

    if not node.shift:
        raise TypeCheckError("[timeshift] Missing shift value")

    # Validate shift format like '1h', '24h', '1d', etc.
    if not re.match(r"^\d+[mhd_ago|w|mo]*", node.shift):
        # This regex is a bit loose but catches basic invalid formats
        # The parser usually ensures this is correct, but let's be safe.
        pass


def _validate_source_field(source: str, field: str | None) -> None:
    """Validate that a field exists for a given data source."""
    if field is None:
        return

    if not is_valid_source_field(source, field):
        raise TypeCheckError(f"Field '{field}' is not valid for source '{source}'")
