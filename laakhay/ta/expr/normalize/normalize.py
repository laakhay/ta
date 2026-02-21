"""Normalization of strategy expression IR.

Passes over the CanonicalExpression to perform:
- source canonicalization
- alias expansion
- positional -> named arg normalization
"""

from ..ir.nodes import CanonicalExpression


def normalize_expression(expr: CanonicalExpression) -> CanonicalExpression:
    """Normalize a canonical expression.

    Currently a placeholder for expanding aliases, canonicalizing symbols,
    and resolving positional to named arguments.
    """
    # TODO: Implement full normalization logic (e.g. recursively visiting nodes
    # to standardize them before typechecking and planning).
    return expr
