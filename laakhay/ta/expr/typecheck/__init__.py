"""Compile-time type constraints and checks."""

from .checker import typecheck_expression, TypeCheckError

__all__ = ["typecheck_expression", "TypeCheckError"]
