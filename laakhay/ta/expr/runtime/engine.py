"""Evaluation engine for expressions and indicators.

Provides a minimal public API per roadmap to evaluate expression graphs
against a dataset of named series.
"""

from __future__ import annotations

from typing import Any

from ...core import Series
from ...core.dataset import Dataset
from ..execution.backend import resolve_backend
from ..ir.nodes import CanonicalExpression, LiteralNode


class Engine:
    """Tiny evaluation engine.

    This initial version evaluates a single expression node against a
    provided dataset. Future versions will add DAG scheduling and caching.
    """

    def __init__(self) -> None:
        self._cache: dict[int, Series[Any]] = {}

    def evaluate(self, expression: CanonicalExpression, dataset: Any) -> Any:
        """Evaluate an expression node with given dataset mapping.

        The dataset should be a mapping from series names used in the
        expression to their corresponding Series objects. Literals are
        supported via Literal nodes internally.
        """
        from ..algebra.operators import Expression

        expr = expression if isinstance(expression, Expression) else Expression(expression)
        plan = expr._ensure_plan()
        backend = resolve_backend()

        result = backend.evaluate(plan, dataset)

        if isinstance(result, dict):
            if len(result) == 1:
                return next(iter(result.values()))
            if len(result) == 0 and isinstance(dataset, Dataset):
                # Allow scalar/literal expressions on empty datasets.
                result = backend.evaluate(plan, {})
            else:
                return result
        if not isinstance(result, Series):
            from ..algebra.scalar_helpers import _make_scalar_series

            return _make_scalar_series(result)
        return result

    def literal(self, value: Any) -> LiteralNode:
        """Create a literal node for convenience."""
        return LiteralNode(value)
