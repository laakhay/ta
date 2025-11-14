"""Expression utilities for parsing, validating, and previewing strategy expressions."""

from __future__ import annotations

from typing import Any

__all__ = [
    "preview",
    "PreviewResult",
    "validate",
    "ValidationResult",
    "ExprValidationError",
]


def __getattr__(name: str) -> Any:
    """Lazy import from runtime to avoid circular imports."""
    if name in ("preview", "PreviewResult", "validate", "ValidationResult", "ExprValidationError"):
        from .runtime import (
            ExprValidationError,
            PreviewResult,
            ValidationResult,
            preview,
            validate,
        )

        if name == "preview":
            return preview
        elif name == "PreviewResult":
            return PreviewResult
        elif name == "validate":
            return validate
        elif name == "ValidationResult":
            return ValidationResult
        elif name == "ExprValidationError":
            return ExprValidationError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
