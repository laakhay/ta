"""Indicator handle and supporting constructs."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core import Dataset, Series
from ..core.types import Price
from ..expr.algebra import Expression, as_expression
from ..expr.algebra.models import (
    BinaryOp,
    ExpressionNode,
    Literal,
    OperatorType,
    UnaryOp,
)
from ..expr.planner.types import SignalRequirements
from ..registry.models import SeriesContext
from ..registry.registry import get_global_registry

# Touch registry to ensure indicators register on import.
_ = get_global_registry()


class IndicatorNode(ExpressionNode):
    """Expression node representing an indicator handle for DAG composition."""

    def __init__(self, name: str, params: dict[str, Any], input_series: ExpressionNode | None = None):
        self.name = name
        self.params = params
        self.input_series = input_series  # Optional input series expression node
        self._registry = get_global_registry()

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        if self.name not in self._registry._indicators:
            raise ValueError(f"Indicator '{self.name}' not found in registry")
        indicator_func = self._registry._indicators[self.name]

        # If input_series is provided, evaluate it first and use it to build context
        if self.input_series is not None:
            # Evaluate the input series expression
            # If it's a SourceExpression, we need to use the evaluator's method
            from ..expr.algebra.models import SourceExpression

            if isinstance(self.input_series, SourceExpression):
                # Use the evaluator's method to resolve SourceExpression
                from ..expr.planner.evaluator import Evaluator

                evaluator = Evaluator()
                # The method only needs expr and context - it extracts symbol/timeframe from expr itself
                input_series_result = evaluator._evaluate_source_expression(self.input_series, context)
            else:
                # For other expression types, evaluate normally
                input_series_result = self.input_series.evaluate(context)
            # Create context with the input series as 'close' (or appropriate field)
            # Most indicators expect 'close' by default
            ctx = SeriesContext(close=input_series_result)
            # Remove input_series from params before calling indicator
            params_without_input = {k: v for k, v in self.params.items() if k != "input_series"}
            return indicator_func(ctx, **params_without_input)

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
        # Extract input_series if present in params (don't mutate self.params)
        input_series = self.params.get("input_series")
        if isinstance(input_series, ExpressionNode):
            # Remove it from params copy
            params_without_input = {k: v for k, v in self.params.items() if k != "input_series"}
            return Expression(IndicatorNode(self.name, params_without_input, input_series=input_series))
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
