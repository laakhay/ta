"""Indicator handle and supporting constructs."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core import Dataset, Series
from ..core.types import Price
from ..expr.algebra import Expression, as_expression
from ..expr.algebra.operators import _to_node
from ..expr.ir.nodes import CallNode
from ..expr.planner.types import SignalRequirements
from ..registry.models import SeriesContext
from ..registry.registry import get_global_registry

# Touch registry to ensure indicators register on import.
_ = get_global_registry()


class IndicatorHandle:
    """Handle for an indicator that can be called and composed algebraically."""

    def __init__(self, name: str, **params: Any):
        self.name = name
        self.params: dict[str, Any] = params
        self._registry = get_global_registry()

        if name not in self._registry._indicators:
            # Ensure indicators are loaded
            import importlib

            try:
                importlib.import_module("laakhay.ta.indicators")
            except Exception:
                pass

            # Ensure namespace helpers (e.g., select/source) are registered
            namespace_module = importlib.import_module("laakhay.ta.api.namespace")
            ensure_func = getattr(namespace_module, "ensure_namespace_registered", None)
            if callable(ensure_func):
                ensure_func()

            if name not in self._registry._indicators:
                # Provide better error message with available indicators
                available = sorted(self._registry.list_all_names()) if hasattr(self._registry, "list_all_names") else []
                msg = f"Indicator '{name}' not found in registry"
                if available:
                    similar = [n for n in available if name.lower() in n.lower() or n.lower() in name.lower()][:3]
                    if similar:
                        msg += f". Did you mean: {', '.join(similar)}?"
                    else:
                        msg += f". Available indicators: {', '.join(available[:10])}"
                        if len(available) > 10:
                            msg += f", ... ({len(available) - 10} more)"
                raise ValueError(msg)

        self._registry_handle = self._registry._indicators[name]
        self._schema = self._get_schema()

    def _get_schema(self) -> dict[str, Any]:
        registry_schema = self._registry_handle.schema
        return {
            "name": self.name,
            "params": self.params,
            "description": getattr(self._registry_handle.func, "__doc__", "No description available"),
            "output_metadata": getattr(registry_schema, "output_metadata", {}),
        }

    def __call__(self, dataset: Dataset | Series[Price]) -> Series[Price]:
        if isinstance(dataset, Series):
            ctx = SeriesContext(close=dataset)
        else:
            ctx = dataset.to_context()
        return self._registry_handle(ctx, **self.params)

    def run(self, data: Dataset | Series[Price]) -> Series[Price] | dict[tuple[str, str, str], Series[Price]]:
        """Evaluate on Series or Dataset via the expression engine."""
        expr = self._to_expression()
        return expr.run(data)

    def _to_expression(self) -> Expression:
        kwargs = {k: _to_node(v) for k, v in self.params.items() if k != "input_series"}
        args = []
        input_series = self.params.get("input_series")
        if input_series is not None:
            args.append(_to_node(input_series))
        return Expression(CallNode(name=self.name, args=tuple(args), kwargs=kwargs))

    # Attributes forwarding to Expression  ----------------------------------

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        return self._to_expression().evaluate(context)

    def dependencies(self) -> list[str]:
        return self._to_expression().dependencies()

    def describe(self) -> str:
        return self._to_expression().describe()

    def requirements(self) -> SignalRequirements:
        return self._to_expression().requirements()

    # Algebraic operators -------------------------------------------------------------------

    def __add__(self, other: Any) -> Expression:
        return self._to_expression() + other

    def __sub__(self, other: Any) -> Expression:
        return self._to_expression() - other

    def __mul__(self, other: Any) -> Expression:
        return self._to_expression() * other

    def __truediv__(self, other: Any) -> Expression:
        return self._to_expression() / other

    def __mod__(self, other: Any) -> Expression:
        return self._to_expression() % other

    def __pow__(self, other: Any) -> Expression:
        return self._to_expression() ** other

    def __lt__(self, other: Any) -> Expression:
        return self._to_expression() < other

    def __gt__(self, other: Any) -> Expression:
        return self._to_expression() > other

    def __le__(self, other: Any) -> Expression:
        return self._to_expression() <= other

    def __ge__(self, other: Any) -> Expression:
        return self._to_expression() >= other

    def __eq__(self, other: Any) -> Expression:  # type: ignore[override]
        return self._to_expression() == other

    def __ne__(self, other: Any) -> Expression:  # type: ignore[override]
        return self._to_expression() != other

    def __and__(self, other: Any) -> Expression:
        return self._to_expression() & other

    def __or__(self, other: Any) -> Expression:
        return self._to_expression() | other

    def __invert__(self) -> Expression:
        return ~self._to_expression()

    def __neg__(self) -> Expression:
        return -self._to_expression()

    def __pos__(self) -> Expression:
        return +self._to_expression()

    @property
    def schema(self) -> dict[str, Any]:
        return self._schema


def _to_expression(
    value: Expression | IndicatorHandle | Series[Any] | float | int | Decimal,
) -> Expression:
    """Convert a value to an Expression for algebraic composition."""
    if isinstance(value, Expression):
        return value
    if isinstance(value, IndicatorHandle):
        return value._to_expression()
    if isinstance(value, Series):
        return as_expression(value)
    if isinstance(value, Decimal):
        value = float(value)
    from ..expr.ir.nodes import LiteralNode
    return Expression(LiteralNode(value))


__all__ = [
    "IndicatorHandle",
]
