"""Namespace helpers (`ta.indicator`, `ta.literal`, `TASeries`)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core import Series
from ..core.types import Price
from ..expressions import Expression, as_expression
from ..expressions.models import Literal
from ..registry.models import SeriesContext
from ..registry.registry import get_global_registry
from .handle import IndicatorHandle


def indicator(name: str, **params: Any) -> IndicatorHandle:
    return IndicatorHandle(name, **params)


def literal(value: float | int | Decimal) -> Expression:
    if isinstance(value, Decimal):
        value = float(value)
    return Expression(Literal(value))


class TANamespace:
    """Main API namespace (e.g., `ta.indicator`, `ta.literal`)."""

    def __init__(self):
        self.indicator = indicator
        self.literal = literal

    def __call__(self, series: Series[Price], **additional_series: Series[Any]) -> TASeries:
        return TASeries(series, **additional_series)

    def __getattr__(self, name: str) -> Any:
        registry = get_global_registry()
        handle = registry.get(name) if hasattr(registry, "get") else None

        if handle is None:
            import importlib
            import sys

            try:
                importlib.import_module("laakhay.ta.indicators")
            except Exception:
                pass
            for module_name in list(sys.modules.keys()):
                if module_name.startswith("laakhay.ta.indicators.") and module_name != "laakhay.ta.indicators.__init__":
                    importlib.reload(sys.modules[module_name])
            handle = registry.get(name) if hasattr(registry, "get") else None

        if handle is not None:
            def factory(**params: Any) -> IndicatorHandle:
                return IndicatorHandle(name, **params)
            return factory

        raise AttributeError(f"Indicator '{name}' not found")


class TASeries:
    """Adapter exposing indicator methods on a base series."""

    def __init__(self, series: Series[Price], **additional_series: Series[Any]):
        self._primary_series = series
        self._additional_series = additional_series
        self._context = SeriesContext(close=series, **additional_series)
        self._registry = get_global_registry()

    def __getattr__(self, name: str) -> Any:
        if name not in self._registry._indicators:
            import importlib
            import sys

            for module_name in list(sys.modules.keys()):
                if module_name.startswith("laakhay.ta.indicators.") and module_name != "laakhay.ta.indicators.__init__":
                    importlib.reload(sys.modules[module_name])

        if name in self._registry._indicators:
            indicator_func = self._registry._indicators[name]

            def indicator_wrapper(*args: Any, **kwargs: Any) -> Expression:
                result = indicator_func(self._context, *args, **kwargs)
                return as_expression(result)

            return indicator_wrapper

        raise AttributeError(f"Indicator '{name}' not found")

    # Arithmetic/logical proxy methods
    def __add__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) + other

    def __sub__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) - other

    def __mul__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) * other

    def __truediv__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) / other

    def __mod__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) % other

    def __pow__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) ** other

    def __lt__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) < other

    def __gt__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) > other

    def __le__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) <= other

    def __ge__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) >= other

    def __eq__(self, other: Any) -> Expression:  # type: ignore[override]
        return as_expression(self._primary_series) == other

    def __ne__(self, other: Any) -> Expression:  # type: ignore[override]
        return as_expression(self._primary_series) != other

    def __and__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) & other

    def __or__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) | other

    def __invert__(self) -> Expression:
        return ~as_expression(self._primary_series)

    def __neg__(self) -> Expression:
        return -as_expression(self._primary_series)

    def __pos__(self) -> Expression:
        return +as_expression(self._primary_series)


ta = TANamespace()


__all__ = [
    "indicator",
    "literal",
    "TANamespace",
    "TASeries",
    "ta",
]
