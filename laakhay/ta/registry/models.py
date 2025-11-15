"""Models for indicator registry system."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from inspect import Signature
from typing import Any

from ..core.series import Series
from .schemas import IndicatorSchema


@dataclass(frozen=True)
class SeriesContext:
    """Context for indicator execution, providing access to input series."""

    def __init__(self, **series: Series[Any]) -> None:
        """Initialize context with named series."""
        object.__setattr__(self, "_series", series)

    def __getattr__(self, name: str) -> Series[Any]:
        """Get a series by name."""
        if name.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        series_dict = self._series
        if name not in series_dict:
            raise AttributeError(f"Series '{name}' not found in context")
        return series_dict[name]

    @property
    def available_series(self) -> list[str]:
        """Get list of available series names."""
        series_dict = self._series
        return list(series_dict.keys())


@dataclass(frozen=True)
class IndicatorHandle:
    """Handle for a registered indicator."""

    name: str
    func: Callable[..., Series[Any]]
    signature: Signature
    schema: IndicatorSchema
    aliases: list[str]

    def __call__(self, *args: Any, **kwargs: Any) -> Series[Any]:
        """Call the indicator function."""
        return self.func(*args, **kwargs)

    def with_overrides(self, **overrides: Any) -> IndicatorHandle:
        """Create a new handle with parameter overrides for partial application."""
        # Validate overrides against schema
        for param_name, value in overrides.items():
            if param_name not in self.schema.parameters:
                raise ValueError(f"Unknown parameter '{param_name}' for indicator '{self.name}'")

            param_schema = self.schema.parameters[param_name]

            expected_type = param_schema.type

            # Skip runtime isinstance checks for typing.Any
            if expected_type is Any:
                continue

            # Handle None values for optional parameters
            if value is None and not param_schema.required:
                continue  # Allow None for optional parameters

            if not isinstance(value, expected_type):
                # Allow some type coercion for common cases
                if expected_type == int and isinstance(value, float | str):
                    try:
                        overrides[param_name] = int(value)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Parameter '{param_name}' expects {expected_type.__name__}, got {type(value).__name__}"
                        )
                elif expected_type == float and isinstance(value, int | str):
                    try:
                        overrides[param_name] = float(value)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Parameter '{param_name}' expects {expected_type.__name__}, got {type(value).__name__}"
                        )
                else:
                    raise ValueError(
                        f"Parameter '{param_name}' expects {expected_type.__name__}, got {type(value).__name__}"
                    )

        # Create a partially applied function
        def partial_func(*args: Any, **kwargs: Any) -> Series[Any]:
            # Merge overrides with kwargs (kwargs take precedence)
            merged_kwargs: dict[str, Any] = {**overrides, **kwargs}
            return self.func(*args, **merged_kwargs)

        # Create new handle with the partially applied function
        return IndicatorHandle(
            name=self.name,
            func=partial_func,  # type: ignore[arg-type]
            signature=self.signature,
            schema=self.schema,
            aliases=self.aliases,
        )
