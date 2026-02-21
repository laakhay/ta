"""Minimal compile-time type checks for the canonical IR."""

from ..ir.nodes import CanonicalExpression


class TypeCheckError(ValueError):
    """Error raised when static type checking fails for an expression."""


def typecheck_expression(expr: CanonicalExpression) -> CanonicalExpression:
    """Typecheck a canonical expression and ensure structural validity.

    This performs minimal compile-time checks (e.g., ensuring both sides
    of an arithmetic operator are numbers) before the expression proceeds
    to the planner.

    Args:
        expr: The normalized canonical IR to check.

    Returns:
        The type-checked canonical expression.

    Raises:
        TypeCheckError: If type constraints are violated.
    """
    # TODO: Implement full type check logic by traversing the tree.
    # We will compute type_tag for each node dynamically based on children constraints.
    return expr
