"""Compile-time type constraints and checks."""

from .checker import TypeCheckError, typecheck_expression

__all__ = ["typecheck_expression", "TypeCheckError"]
