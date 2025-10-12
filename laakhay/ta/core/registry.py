from __future__ import annotations

from .base import BaseIndicator

# Global registry for indicator CLASSES (stateless).
INDICATORS: dict[str, type[BaseIndicator]] = {}


def register(indicator_cls: type[BaseIndicator]) -> None:
    """Register an indicator CLASS under its .name (overwrites if exists)."""
    name = getattr(indicator_cls, "name", None)
    if not name or not isinstance(name, str):
        raise ValueError("Indicator class must define a non-empty 'name' ClassVar[str]")
    INDICATORS[name] = indicator_cls


def get_indicator(name: str) -> type[BaseIndicator] | None:
    """Retrieve indicator class by name."""
    return INDICATORS.get(name)


def list_indicators() -> list[str]:
    """List all registered indicator names."""
    return sorted(INDICATORS.keys())
