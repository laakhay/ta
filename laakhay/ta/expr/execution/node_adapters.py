"""Shared node-level step adapters for execution backends."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ...core.series import Series
from ...primitives.adapters.registry_binding import coerce_incremental_input, resolve_kernel_for_indicator
from ..ir.nodes import (
    AggregateNode,
    BinaryOpNode,
    CallNode,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
)
from .time_shift import parse_shift_periods


def eval_source_ref_step(node: SourceRefNode, tick: dict[str, Any]) -> Decimal | None:
    """Evaluate a source reference for one tick update."""
    key1 = f"{node.source}.{node.field}"
    key2 = node.field
    if key1 in tick:
        return Decimal(str(tick[key1]))
    if key2 in tick:
        return Decimal(str(tick[key2]))
    return None


def eval_literal_step(node: LiteralNode) -> Any:
    """Evaluate a literal for one tick update."""
    if isinstance(node.value, Series) and len(node.value) == 1:
        return Decimal(str(node.value.values[0]))
    if isinstance(node.value, str):
        return node.value
    return Decimal(str(node.value)) if node.value is not None else None


def eval_binary_step(node: BinaryOpNode, children_vals: list[Any]) -> Any:
    """Evaluate a binary operator for one tick update."""
    if len(children_vals) < 2 or children_vals[0] is None or children_vals[1] is None:
        return None
    left, right = children_vals[0], children_vals[1]
    op = node.operator
    if op == "add":
        return left + right
    if op == "sub":
        return left - right
    if op == "mul":
        return left * right
    if op == "div":
        return left / right if right != 0 else Decimal(0)
    if op == "eq":
        return Decimal(1) if left == right else Decimal(0)
    if op == "gt":
        return Decimal(1) if left > right else Decimal(0)
    if op == "lt":
        return Decimal(1) if left < right else Decimal(0)
    return None


def eval_unary_step(node: UnaryOpNode, child_val: Any) -> Any:
    if child_val is None:
        return None
    if node.operator == "neg":
        return -child_val
    if node.operator == "pos":
        return child_val
    if node.operator == "not":
        return Decimal(0) if _truthy(child_val) else Decimal(1)
    return None


def eval_filter_step(node: FilterNode, children_vals: list[Any]) -> Any:
    if len(children_vals) < 2:
        return None
    value, condition = children_vals[0], children_vals[1]
    if value is None or condition is None:
        return None
    return value if _truthy(condition) else None


def eval_aggregate_step(node: AggregateNode, child_val: Any, state: Any) -> Any:
    op = node.operation.lower()
    stats = state.algorithm_state
    if not isinstance(stats, dict):
        stats = {"count": 0, "sum": Decimal(0), "max": None, "min": None}

    if child_val is not None:
        v = Decimal(str(child_val))
        stats["count"] += 1
        stats["sum"] += v
        stats["max"] = v if stats["max"] is None else max(stats["max"], v)
        stats["min"] = v if stats["min"] is None else min(stats["min"], v)

    state.algorithm_state = stats

    if op == "count":
        return Decimal(stats["count"])
    if op == "sum":
        return stats["sum"]
    if op == "avg":
        return None if stats["count"] == 0 else (stats["sum"] / Decimal(stats["count"]))
    if op == "max":
        return stats["max"]
    if op == "min":
        return stats["min"]
    return None


def eval_time_shift_step(node: TimeShiftNode, child_val: Any, state: Any) -> Any:
    if child_val is None:
        return None

    periods = parse_shift_periods(node.shift)
    history = state.algorithm_state
    if not isinstance(history, list):
        history = []

    output: Any = None
    if len(history) >= periods:
        prev = history[-periods]
        current = Decimal(str(child_val))
        prev_dec = Decimal(str(prev))
        if node.operation == "change":
            output = current - prev_dec
        elif node.operation == "change_pct":
            output = Decimal(0) if prev_dec == 0 else ((current - prev_dec) / prev_dec) * Decimal(100)
        elif node.operation is None:
            output = prev_dec

    history.append(child_val)
    if len(history) > periods + 1:
        history.pop(0)
    state.algorithm_state = history
    return output


def eval_call_step(node: CallNode, children_vals: list[Any], tick: dict[str, Any], state: Any) -> Any:
    from ...registry.registry import get_global_registry

    registry = get_global_registry()
    name = node.name
    kwargs = _resolve_call_kwargs(node, children_vals, registry)

    input_val = children_vals[0] if children_vals else None
    if input_val is None:
        return None

    if state.algorithm_state is None:
        kernel = resolve_kernel_for_indicator(name)
        if kernel is None:
            return None
        state.algorithm_state = kernel.initialize([], **kwargs)
        state._kernel_instance = kernel

    kernel = state._kernel_instance
    input_val = coerce_incremental_input(name, input_val, tick, state.algorithm_state)
    new_alg_state, out_val = kernel.step(state.algorithm_state, input_val, **kwargs)
    state.algorithm_state = new_alg_state
    return out_val


def _resolve_call_kwargs(node: CallNode, children_vals: list[Any], registry: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    handle = registry.get(node.name)
    if not handle:
        kwarg_vals = children_vals[1 + len(node.args) :]
        for key, val in zip(sorted(node.kwargs.keys()), kwarg_vals, strict=False):
            kwargs[key] = val
        return kwargs

    import inspect

    sig = inspect.signature(handle.func)
    param_names = [p.name for p in sig.parameters.values() if p.name != "ctx"]
    arg_vals = children_vals[1 : 1 + len(node.args)] if len(children_vals) > 1 else []
    for i, val in enumerate(arg_vals):
        if i < len(param_names):
            kwargs[param_names[i]] = val

    kwarg_vals = children_vals[1 + len(node.args) :]
    for key, val in zip(sorted(node.kwargs.keys()), kwarg_vals, strict=False):
        kwargs[key] = val

    for p in sig.parameters.values():
        if p.name != "ctx" and p.name not in kwargs and p.default is not inspect.Parameter.empty:
            kwargs[p.name] = p.default
    return kwargs


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return bool(Decimal(str(value)))
    try:
        return bool(Decimal(str(value)))
    except Exception:
        return bool(value)
