from __future__ import annotations

from typing import Any

from ..core import Series
from ..registry.models import SeriesContext
from .backend import is_rust_backend


def dispatch_indicator_call(
    indicator_func: Any,
    eval_args: list[Any],
    eval_kwargs: dict[str, Any],
    context: dict[str, Any],
    has_input_expr: bool,
) -> Any:
    """Fast-path dispatch for indicator call execution.

    This keeps call-shape handling in one place and is the central hook for
    Rust-first execution policy in evaluator hot paths.
    """
    if not is_rust_backend():
        return _call_with_context(indicator_func, eval_args, eval_kwargs, context, has_input_expr)

    # Rust default path currently keeps indicator API contract intact while
    # reducing per-node branching in evaluator.
    return _call_with_context(indicator_func, eval_args, eval_kwargs, context, has_input_expr)


def _call_with_context(
    indicator_func: Any,
    eval_args: list[Any],
    eval_kwargs: dict[str, Any],
    context: dict[str, Any],
    has_input_expr: bool,
) -> Any:
    if has_input_expr and len(eval_args) > 0:
        input_series_result = eval_args[0]
        remaining_args = eval_args[1:]

        if isinstance(input_series_result, Series):
            return indicator_func(SeriesContext(close=input_series_result), *remaining_args, **eval_kwargs)

        base_ctx = SeriesContext(**context)
        return indicator_func(base_ctx, input_series_result, *remaining_args, **eval_kwargs)

    return indicator_func(SeriesContext(**context), *eval_args, **eval_kwargs)


__all__ = ["dispatch_indicator_call"]
