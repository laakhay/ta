"""Evaluation engine for expressions and indicators.

Provides a minimal public API per roadmap to evaluate expression graphs
against a dataset of named series.
"""

from __future__ import annotations

from typing import Any, Dict

from .core import Series
from .expressions.models import ExpressionNode, Literal


class Engine:
    """Tiny evaluation engine.

    This initial version evaluates a single expression node against a
    provided dataset. Future versions will add DAG scheduling and caching.
    """

    def __init__(self) -> None:
        self._cache: Dict[int, Series[Any]] = {}

    def evaluate(self, expression: ExpressionNode, dataset: Dict[str, Series[Any]]) -> Series[Any]:
        """Evaluate an expression node with given dataset mapping.

        The dataset should be a mapping from series names used in the
        expression to their corresponding Series objects. Literals are
        supported via Literal nodes internally.
        """
        # Simple direct evaluation; placeholder for future caching/DAG walk
        return expression.evaluate(dataset)

    def literal(self, value: Any) -> Literal:
        """Create a literal node for convenience."""
        return Literal(value)


