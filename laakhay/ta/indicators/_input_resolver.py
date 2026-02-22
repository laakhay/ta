"""Resolve series-like inputs (Expression, CallNode, Series, scalar) to Series.

This module is the single boundary between indicators and the expression engine.
Indicators that accept Expression/IR nodes delegate resolution here, keeping
indicator logic primitive-based and decoupled from expression recursion.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from ..core import Series
from ..core.series import align_series
from ..core.types import Price
from ..primitives.select import _select
from ..registry.models import SeriesContext

if TYPE_CHECKING:
    from ..expr.algebra.operators import Expression
    from ..expr.ir.nodes import CallNode


def resolve_series_input(
    value: Series[Price] | Expression | CallNode | float | int | Decimal | None,
    ctx: SeriesContext,
    *,
    reference_series: Series[Price] | None = None,
) -> Series[Price]:
    """Resolve a series-like input to a Series.

    Handles:
    - None: returns default from ctx (close/price)
    - Series: returns as-is
    - Expression / CallNode: evaluates via expression engine (single boundary)
    - int, float, Decimal: constant series matching reference timestamps
    """
    if value is None:
        return _select(ctx)

    if isinstance(value, Series):
        return value

    # Expression or CallNode (IR): evaluate via expression engine
    if _is_expression_or_node(value):
        return _evaluate_expression(value, ctx, reference_series)

    if isinstance(value, (int, float, Decimal)):
        ref = reference_series if reference_series is not None else _select(ctx)
        return Series[Price](
            timestamps=ref.timestamps,
            values=tuple(Decimal(str(value)) for _ in ref.timestamps),
            symbol=ref.symbol,
            timeframe=ref.timeframe,
        )

    raise TypeError(f"Unsupported type for series input: {type(value)}")


def _is_expression_or_node(value: Any) -> bool:
    """Check if value is Expression or CallNode without importing at module load."""
    if value is None:
        return False
    name = type(value).__name__
    return name == "Expression" or name == "CallNode"


def _evaluate_expression(
    expr: Any,
    ctx: SeriesContext,
    reference_series: Series[Price] | None,
) -> Series[Price]:
    """Evaluate Expression or CallNode against context. Single expression-engine boundary."""
    from ..expr.algebra.operators import Expression
    from ..expr.ir.nodes import CallNode

    base_series = reference_series if reference_series is not None else _select(ctx)
    context_dict: dict[str, Series[Price]] = {}
    for field_name in ctx.available_series:
        series = getattr(ctx, field_name)
        if len(series) != len(base_series):
            try:
                _, aligned_series = align_series(base_series, series, how="inner")
                context_dict[field_name] = aligned_series
            except ValueError:
                context_dict[field_name] = series
        else:
            context_dict[field_name] = series

    # Wrap CallNode in Expression for evaluation
    if isinstance(expr, CallNode):
        expr = Expression(expr)

    result = expr.evaluate(context_dict)
    if not isinstance(result, Series):
        raise TypeError(f"Expression evaluated to {type(result)}, expected Series")
    return result


def resolve_channel_tuple(
    value: Any,
    ctx: SeriesContext,
    reference_series: Series[Price] | None = None,
) -> tuple[Series[Price], Series[Price]] | None:
    """Extract (upper, lower) from a tuple-returning indicator (e.g. bbands)."""
    if isinstance(value, tuple) and len(value) >= 3:
        upper, lower = value[0], value[2]
        if isinstance(upper, Series) and isinstance(lower, Series):
            return upper, lower
        return None

    if not _is_expression_or_node(value):
        return None

    base_series = reference_series if reference_series is not None else _select(ctx)
    context_dict: dict[str, Series[Price]] = {}
    for field_name in ctx.available_series:
        series = getattr(ctx, field_name)
        if len(series) != len(base_series):
            try:
                _, aligned_series = align_series(base_series, series, how="inner")
                context_dict[field_name] = aligned_series
            except ValueError:
                context_dict[field_name] = series
        else:
            context_dict[field_name] = series

    from ..expr.algebra.operators import Expression
    from ..expr.ir.nodes import CallNode

    if isinstance(value, CallNode):
        value = Expression(value)
    result = value.evaluate(context_dict)
    if not isinstance(result, tuple) or len(result) < 3:
        return None
    upper, lower = result[0], result[2]
    if isinstance(upper, Series) and isinstance(lower, Series):
        return upper, lower
    return None
