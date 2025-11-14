"""Namespace helpers (`ta.indicator`, `ta.literal`, `TASeries`)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Tuple

from ..core import Dataset, Series
from ..core.types import Price
from ..expr.algebra import Expression, as_expression
from ..expr.algebra.models import Literal
from ..primitives import _select_field  # Import the function that handles derived fields
from ..registry import register
from ..registry.models import SeriesContext
from ..registry.registry import get_global_registry
from .handle import IndicatorHandle


def _ensure_indicators_loaded() -> None:
    """Ensure indicators module is imported, registering all indicators.

    This is idempotent - importing an already-imported module is safe.
    Python's import cache ensures the module is only executed once.

    If the registry has been cleared (e.g., in tests), this will attempt to
    re-register indicators by importing the module, which should trigger
    the registration decorators again. However, since decorators only run
    once per import, we need to explicitly call the registration functions.
    """
    import importlib

    from ..registry.registry import get_global_registry

    registry = get_global_registry()

    # Check if registry is empty or missing common indicators
    # If so, we need to re-register
    common_indicators = ["sma", "ema", "rsi", "select"]
    has_indicators = any(name in registry._indicators for name in common_indicators)

    if not has_indicators:
        # Registry might have been cleared - try to re-import indicators
        # This will only work if modules haven't been imported yet
        try:
            importlib.import_module("laakhay.ta.indicators")
            # Also ensure namespace helpers are registered
            ensure_namespace_registered()
        except Exception:
            # If import fails, silently fail - will be caught later with better error message
            pass
    else:
        # Registry has indicators, but ensure namespace helpers are registered
        ensure_namespace_registered()


_TIMEFRAME_MULTIPLIERS: dict[str, int] = {
    "m": 1,
    "h": 60,
    "d": 60 * 24,
    "w": 60 * 24 * 7,
}

_SELECT_DESCRIPTION = "Select a field from the evaluation context"
_SELECT_OUTPUT_METADATA = {"result": {"type": "price", "role": "selector", "polarity": "neutral"}}


@register("select", description=_SELECT_DESCRIPTION, output_metadata=_SELECT_OUTPUT_METADATA)
def _select_indicator(ctx: SeriesContext, field: str) -> Series[Any]:
    """Select a field from the context, supporting both standard and derived fields."""
    # Use _select_field from primitives which handles derived fields (hlc3, ohlc4, etc.)
    return _select_field(ctx, field)


def ensure_namespace_registered() -> None:
    """Re-register namespace helpers if the global registry was cleared."""
    registry = get_global_registry()
    if "select" not in registry._indicators:
        # Re-apply the decorator to register the select helper without reloading modules.
        register(
            "select",
            description=_SELECT_DESCRIPTION,
            output_metadata=_SELECT_OUTPUT_METADATA,
        )(_select_indicator)


def indicator(name: str, **params: Any) -> IndicatorHandle:
    return IndicatorHandle(name, **params)


def literal(value: float | int | Decimal | Series[Any]) -> Expression:
    if isinstance(value, Series):
        return as_expression(value)
    if isinstance(value, Decimal):
        value = float(value)
    return Expression(Literal(value))


def source(field: str) -> Expression:
    """Create an expression that selects a field from the dataset context.

    Example
    -------
    >>> close = ta.source("close")
    >>> signal = (ta.sma(close, 20) > 10) & (ta.rsi(close, 14) > 50)
    """
    handle = indicator("select", field=field)
    return handle._to_expression()


def ref(
    dataset: Dataset,
    *,
    timeframe: str,
    field: str = "close",
    symbol: str | None = None,
    reference: Series[Any] | Tuple[str, str, str] | None = None,
    fill: str = "ffill",
) -> Series[Any]:
    """Fetch a field from a specific timeframe and optionally align it to a reference series.

    Args:
        dataset: Dataset containing the source data.
        timeframe: Timeframe to pull the field from (e.g., "4h").
        field: Field name, default "close".
        symbol: Optional symbol filter; defaults to the dataset symbol when omitted.
        reference: Optional reference series (or tuple describing where to fetch it:
            ``(symbol, timeframe, field)``) used to align the result via ``sync_timeframe``.
        fill: Fill strategy passed to ``sync_timeframe`` when ``reference`` is provided.

    Returns:
        Series aligned to the requested timeframe (or synced to the reference timeframe).
    """
    view = dataset.select(symbol=symbol, timeframe=timeframe)
    ctx = view.to_context()

    if field not in ctx.available_series:
        raise ValueError(f"Field '{field}' not found for timeframe '{timeframe}'. Available: {ctx.available_series}")

    series = getattr(ctx, field)

    if reference is None:
        return series

    if isinstance(reference, tuple):
        ref_symbol, ref_timeframe, ref_field = reference
        ref_view = dataset.select(symbol=ref_symbol, timeframe=ref_timeframe)
        ref_ctx = ref_view.to_context()
        if ref_field not in ref_ctx.available_series:
            raise ValueError(
                f"Reference field '{ref_field}' not found for timeframe '{ref_timeframe}'. "
                f"Available: {ref_ctx.available_series}"
            )
        reference_series = getattr(ref_ctx, ref_field)
    elif isinstance(reference, Series):
        reference_series = reference
    else:
        raise TypeError("reference must be either a Series or a (symbol, timeframe, field) tuple")

    sync_handle = indicator("sync_timeframe", fill=fill, reference=reference_series)
    return sync_handle(series)


def _timeframe_to_minutes(label: str) -> int:
    if not isinstance(label, str) or len(label) < 2:
        raise ValueError(f"Invalid timeframe label: {label!r}")
    unit = label[-1].lower()
    magnitude = label[:-1]
    if unit not in _TIMEFRAME_MULTIPLIERS:
        raise ValueError(f"Unsupported timeframe unit '{unit}' in {label!r}")
    try:
        value = int(magnitude)
    except ValueError as exc:
        raise ValueError(f"Invalid timeframe magnitude in {label!r}") from exc
    if value <= 0:
        raise ValueError("Timeframe magnitude must be positive")
    return value * _TIMEFRAME_MULTIPLIERS[unit]


def resample(
    dataset: Dataset,
    *,
    from_timeframe: str,
    to_timeframe: str,
    field: str = "close",
    symbol: str | None = None,
    agg: str = "last",
) -> Series[Any] | dict[str, Series[Any]]:
    """Resample a field from one timeframe to another using downsample primitives."""
    source_minutes = _timeframe_to_minutes(from_timeframe)
    target_minutes = _timeframe_to_minutes(to_timeframe)
    if target_minutes % source_minutes != 0:
        raise ValueError(
            f"Cannot resample from {from_timeframe} to {to_timeframe}: "
            f"{to_timeframe} is not an integer multiple of {from_timeframe}"
        )
    factor = target_minutes // source_minutes
    if factor < 1:
        raise ValueError("Target timeframe must be greater than or equal to source timeframe")

    target_param = "ohlcv" if field.lower() == "ohlcv" else field
    handle = indicator(
        "downsample",
        factor=int(factor),
        agg=agg,
        target=target_param,
        target_timeframe=to_timeframe,
    )
    view = dataset.select(symbol=symbol, timeframe=from_timeframe)
    return handle(view)


class TANamespace:
    """Main API namespace (e.g., `ta.indicator`, `ta.literal`)."""

    def __init__(self):
        self.indicator = indicator
        self.literal = literal
        self.ref = ref
        self.resample = resample

    def __call__(self, series: Series[Price], **additional_series: Series[Any]) -> TASeries:
        return TASeries(series, **additional_series)

    def __getattr__(self, name: str) -> Any:
        if name == "register":
            from ..registry.registry import register as _register  # avoid cycle

            return _register

        # Ensure indicators are loaded
        _ensure_indicators_loaded()

        registry = get_global_registry()
        handle = registry.get(name) if hasattr(registry, "get") else None

        if handle is not None:

            def factory(**params: Any) -> IndicatorHandle:
                return IndicatorHandle(name, **params)

            return factory

        # Provide better error message with available indicators
        available = sorted(registry.list_all_names()) if hasattr(registry, "list_all_names") else []
        msg = f"Indicator '{name}' not found"
        if available:
            # Find similar names
            similar = [n for n in available if name.lower() in n.lower() or n.lower() in name.lower()][:3]
            if similar:
                msg += f". Did you mean: {', '.join(similar)}?"
            else:
                msg += f". Available indicators: {', '.join(available[:10])}"
                if len(available) > 10:
                    msg += f", ... ({len(available) - 10} more)"
        raise AttributeError(msg)


class TASeries:
    """Adapter exposing indicator methods on a base series."""

    def __init__(self, series: Series[Price], **additional_series: Series[Any]):
        self._primary_series = series
        self._additional_series = additional_series
        self._context = SeriesContext(close=series, **additional_series)
        self._registry = get_global_registry()

    def __getattr__(self, name: str) -> Any:
        # Ensure indicators are loaded
        _ensure_indicators_loaded()

        if name in self._registry._indicators:
            indicator_func = self._registry._indicators[name]

            def indicator_wrapper(*args: Any, **kwargs: Any) -> Expression:
                result = indicator_func(self._context, *args, **kwargs)
                return as_expression(result)

            return indicator_wrapper

        # Provide better error message with available indicators
        available = sorted(self._registry.list_all_names()) if hasattr(self._registry, "list_all_names") else []
        msg = f"Indicator '{name}' not found"
        if available:
            similar = [n for n in available if name.lower() in n.lower() or n.lower() in name.lower()][:3]
            if similar:
                msg += f". Did you mean: {', '.join(similar)}?"
            else:
                msg += f". Available indicators: {', '.join(available[:10])}"
                if len(available) > 10:
                    msg += f", ... ({len(available) - 10} more)"
        raise AttributeError(msg)

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

# Ensure helper indicators (e.g., select) are present on module import.
ensure_namespace_registered()


__all__ = [
    "indicator",
    "literal",
    "ref",
    "resample",
    "TANamespace",
    "TASeries",
    "ta",
]
