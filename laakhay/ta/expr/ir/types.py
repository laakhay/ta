"""Expression IR types."""

from typing import Literal

# Minimal type tags for compile-time safety checks
ExprType = Literal[
    "series_number",
    "series_bool",
    "scalar_number",
    "scalar_bool",
    "unknown",
]
