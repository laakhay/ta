"""Indicator handle and supporting constructs."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core import Dataset, Series
from ..core.types import Price
from ..expressions import Expression, as_expression
from ..expressions.models import (
    BinaryOp,
    ExpressionNode,
    Literal,
    OperatorType,
    UnaryOp,
)
from ..graph.types import SignalRequirements
from ..registry.models import SeriesContext
from ..registry.registry import get_global_registry

# Touch registry to ensure indicators register on import.
_ = get_global_registry()


class IndicatorNode(ExpressionNode):
    """Expression node representing an indicator handle for DAG composition."""

    def __init__(self, name: str, params: dict[str, Any]):
        self.name = name
        self.params = params
        self._registry = get_global_registry()

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        if self.name not in self._registry._indicators:
            raise ValueError(f"Indicator '{self.name}' not found in registry")
        indicator_func = self._registry._indicators[self.name]
        return indicator_func(SeriesContext(**context), **self.params)

    def dependencies(self) -> list[str]:
        return []

    def describe(self) -> str:
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({params_str})"

    def run(self, context: dict[str, Series[Any]]) -> Series[Any]:
        return self.evaluate(context)


class IndicatorHandle:
    """Handle for an indicator that can be called and composed algebraically."""

    def __init__(self, name: str, **params: Any):
        self.name = name
        self.params: dict[str, Any] = params
        self._registry = get_global_registry()

        if name not in self._registry._indicators:
            import importlib
            import sys

            for module_name in list(sys.modules.keys()):
                if module_name.startswith("laakhay.ta.indicators.") and module_name != "laakhay.ta.indicators.__init__":
                    importlib.reload(sys.modules[module_name])

            # Ensure namespace helpers (e.g., select/source) are registered even if the
            # registry was cleared mid-test. This avoids reloading the module, which
            # would create new class objects and break isinstance checks.
            namespace_module = sys.modules.get("laakhay.ta.api.namespace")
            if namespace_module is None:
                namespace_module = importlib.import_module("laakhay.ta.api.namespace")
            ensure_func = getattr(namespace_module, "ensure_namespace_registered", None)
            if callable(ensure_func):
                ensure_func()

            if name not in self._registry._indicators:
                raise ValueError(f"Indicator '{name}' not found in registry")

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
        return Expression(IndicatorNode(self.name, self.params))

    # ExpressionNode compatibility ----------------------------------------------------------

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        if isinstance(context, dict):
            temp_dataset = Dataset()
            for name, series in context.items():
                temp_dataset.add_series("temp", "1h", series, name)
            return self(temp_dataset)
        return self(context)

    def dependencies(self) -> list[str]:
        return ["close"]

    def describe(self) -> str:
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({params_str})"

    def requirements(self) -> SignalRequirements:
        return self._to_expression().requirements()

    # Algebraic operators -------------------------------------------------------------------

    def __add__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.ADD, self._to_expression()._node, other_expr._node))

    def __sub__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.SUB, self._to_expression()._node, other_expr._node))

    def __mul__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.MUL, self._to_expression()._node, other_expr._node))

    def __truediv__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.DIV, self._to_expression()._node, other_expr._node))

    def __mod__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.MOD, self._to_expression()._node, other_expr._node))

    def __pow__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.POW, self._to_expression()._node, other_expr._node))

    def __lt__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.LT, self._to_expression()._node, other_expr._node))

    def __gt__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.GT, self._to_expression()._node, other_expr._node))

    def __le__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.LE, self._to_expression()._node, other_expr._node))

    def __ge__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.GE, self._to_expression()._node, other_expr._node))

    def __eq__(self, other: Any) -> Expression:  # type: ignore[override]
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.EQ, self._to_expression()._node, other_expr._node))

    def __ne__(self, other: Any) -> Expression:  # type: ignore[override]
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.NE, self._to_expression()._node, other_expr._node))

    def __and__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.AND, self._to_expression()._node, other_expr._node))

    def __or__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.OR, self._to_expression()._node, other_expr._node))

    def __invert__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.NOT, self._to_expression()._node))

    def __neg__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.NEG, self._to_expression()._node))

    def __pos__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.POS, self._to_expression()._node))

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
    return Expression(Literal(value))


__all__ = [
    "IndicatorHandle",
    "IndicatorNode",
]
