"""Type checking of strategy expression IR."""

from typing import Any

from ...registry.registry import get_global_registry
from ..ir.nodes import (
    BinaryOpNode,
    CallNode,
    CanonicalExpression,
    LiteralNode,
    SourceRefNode,
    UnaryOpNode,
)


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
            # Safe coercion: int -> float
            if expected_type is float and isinstance(val, int):
                pass
            else:
                raise TypeCheckError(
                    f"[{indicator_name}] Parameter '{param_name}' expects {expected_type.__name__}, got {type(val).__name__}"
                )

        # Value validation: Periods must be positive
        if param_name.lower() in ("period", "lookback", "fast_period", "slow_period", "signal_period"):
            if isinstance(val, int | float) and val <= 0:
                raise TypeCheckError(f"[{indicator_name}] Parameter '{param_name}' must be positive, got {val}")
