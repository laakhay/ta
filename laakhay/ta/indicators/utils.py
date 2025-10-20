"""Indicator utility functions and common calculations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core import Series
from ..core.types import Price
from ..expressions.operators import Expression
from ..expressions.models import Literal
from ..registry.models import SeriesContext


def _select_source_series(ctx: SeriesContext) -> Series[Price]:
    """Pick a reasonable default source series from the context."""
    names = ctx.available_series
    for candidate in ("price", "close"):
        if candidate in names:
            return getattr(ctx, candidate)
    if not names:
        raise ValueError("SeriesContext has no series to operate on")
    return getattr(ctx, names[0])


def create_expression_from_series(series: Series[Price]) -> Expression:
    """Create an Expression from a Series for use in indicator calculations."""
    return Expression(Literal(series))


def calculate_typical_price(high: Series[Price], low: Series[Price], close: Series[Price]) -> Series[Price]:
    """Calculate typical price (HLC/3) using expressions."""
    # Create expressions for each series
    high_expr = create_expression_from_series(high)
    low_expr = create_expression_from_series(low)
    close_expr = create_expression_from_series(close)
    
    # Calculate (high + low + close) / 3
    sum_expr = high_expr + low_expr + close_expr
    typical_expr = sum_expr / 3
    
    # Evaluate the expression
    context = {}
    return typical_expr.evaluate(context)