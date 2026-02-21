"""Type checking of strategy expression IR."""

from ..ir.nodes import CanonicalExpression


class TypeCheckError(ValueError):
    """Raised when an expression fails static type checking."""

    pass


def typecheck_expression(expr: CanonicalExpression) -> CanonicalExpression:
    """Verify semantic correctness and type safety of an expression.

    Currently a pass-through placeholder.
    """
    return expr
