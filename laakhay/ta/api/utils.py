from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..core import Series


def _call_indicator(
    name: str,
    args: Iterable[Any],
    kwargs: dict[str, Any],
    param_order: tuple[str, ...] = (),
) -> Any:
    """Shared helper that supports both functional and handle-style calls.

    Examples
    --------
    >>> ta.sma(20)                  # returns handle
    >>> ta.sma(series, period=20)   # evaluates on series
    >>> ta.sma(series, 20)          # positional period
    >>> ta.sma(dataset, period=20)  # evaluates on dataset
    """
    from .namespace import indicator

    args = list(args)
    series_or_dataset: Any | None = None
    if args and isinstance(args[0], Series):
        series_or_dataset = args.pop(0)
    elif args and hasattr(args[0], "to_context"):
        # Dataset-like object (duck typing to avoid circular import)
        series_or_dataset = args.pop(0)

    if len(args) > len(param_order):
        raise TypeError(f"Too many positional arguments for indicator '{name}'. Expected at most {len(param_order)}")

    params: dict[str, Any] = {}
    for name_key, value in zip(param_order, args, strict=False):
        if value is not None:
            params[name_key] = value
    params.update(kwargs)

    handle = indicator(name, **params)
    if series_or_dataset is not None:
        return handle(series_or_dataset)
    return handle
