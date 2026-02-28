from __future__ import annotations

from decimal import Decimal

from ..core import Series
from ..core.types import Price
from ..registry.models import SeriesContext
from ..registry.registry import register
from ..registry.schemas import (
    IndicatorSpec,
    OutputSpec,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
)
from .math_ops import ew_binary


def _select(ctx: SeriesContext) -> Series[Price]:
    """Pick a reasonable default source series from the context."""
    for c in ("price", "close"):
        if c in ctx.available_series:
            return getattr(ctx, c)
    if not ctx.available_series:
        raise ValueError("SeriesContext has no series to operate on")
    return getattr(ctx, ctx.available_series[0])


def _select_field(ctx: SeriesContext, field: str) -> Series[Price]:
    """Return a specific field from the context, raising if unavailable."""
    field_lower = field.lower()

    if field_lower in ("hlc3", "typical_price"):
        if (
            "high" not in ctx.available_series
            or "low" not in ctx.available_series
            or "close" not in ctx.available_series
        ):
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'low', 'close'")
        return (ctx.high + ctx.low + ctx.close) / Decimal(3)

    if field_lower in ("ohlc4", "weighted_close"):
        if (
            "open" not in ctx.available_series
            or "high" not in ctx.available_series
            or "low" not in ctx.available_series
            or "close" not in ctx.available_series
        ):
            raise ValueError(
                f"SeriesContext missing required fields for '{field}': need 'open', 'high', 'low', 'close'"
            )
        return (ctx.open + ctx.high + ctx.low + ctx.close) / Decimal(4)

    if field_lower in ("hl2", "median_price"):
        if "high" not in ctx.available_series or "low" not in ctx.available_series:
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'low'")
        return (ctx.high + ctx.low) / Decimal(2)

    if field_lower == "range":
        if "high" not in ctx.available_series or "low" not in ctx.available_series:
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'low'")
        return ctx.high - ctx.low

    if field_lower == "upper_wick":
        if (
            "high" not in ctx.available_series
            or "open" not in ctx.available_series
            or "close" not in ctx.available_series
        ):
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'high', 'open', 'close'")
        return ctx.high - ew_binary(ctx.open, ctx.close, max)

    if field_lower == "lower_wick":
        if (
            "open" not in ctx.available_series
            or "close" not in ctx.available_series
            or "low" not in ctx.available_series
        ):
            raise ValueError(f"SeriesContext missing required fields for '{field}': need 'open', 'close', 'low'")
        return ew_binary(ctx.open, ctx.close, min) - ctx.low

    if field in ctx.available_series:
        return getattr(ctx, field)
    raise ValueError(f"SeriesContext missing required field '{field}'")


_SELECT_SPEC = IndicatorSpec(
    name="select",
    description="Select a named series from the context",
    params={"field": ParamSpec("field", str, default="close", required=False)},
    outputs={"result": OutputSpec(name="result", type=Series, description="Selected series", role="selector")},
    semantics=SemanticsSpec(required_fields=("close",), optional_fields=("field",), default_lookback=1),
    runtime_binding=RuntimeBindingSpec(kernel_id="select"),
)


@register(spec=_SELECT_SPEC)
def select(ctx: SeriesContext, field: str = "close") -> Series[Price]:
    return _select_field(ctx, field)


__all__ = ["_select", "_select_field", "select"]
