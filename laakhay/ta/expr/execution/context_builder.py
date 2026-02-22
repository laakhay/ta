from __future__ import annotations

from typing import Any

from ...core.dataset import Dataset
from ...core.series import Series
from ...exceptions import MissingDataError
from ..ir.nodes import SourceRefNode
from ..planner.types import SignalRequirements


def collect_required_field_names(requirements: SignalRequirements) -> list[str]:
    names = {req.field for req in requirements.data_requirements if req.field}
    if not names:
        names = {"close"}
    return sorted(names)


def build_evaluation_context(
    dataset: Dataset,
    symbol: str,
    timeframe: str,
    required_fields: list[str],
) -> dict[str, Series[Any]]:
    """Build a unified context dict for evaluator execution."""
    try:
        context = dataset.to_multisource_context(symbol=symbol, timeframe=timeframe)
        context_dict: dict[str, Series[Any]] = {name: getattr(context, name) for name in context.available_series}
    except (ValueError, AttributeError):
        # Fallback for datasets without to_multisource_context (e.g. minimal/single-source)
        context = dataset.build_context(symbol, timeframe, required_fields)
        context_dict = {name: getattr(context, name) for name in context.available_series}

    for key, series_obj in dataset:
        if key.symbol != symbol or key.timeframe != timeframe:
            continue

        if hasattr(series_obj, "to_series"):
            field_mapping = {
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
                "price": "close",
            }
            for field, ohlcv_field in field_mapping.items():
                try:
                    field_series = series_obj.to_series(ohlcv_field)
                    context_dict[f"{key.source}.{field}"] = field_series
                    context_dict[field] = field_series
                except (KeyError, AttributeError, ValueError):
                    pass
            continue

        source_name = key.source
        if "_" in source_name:
            parts = source_name.split("_", 1)
            base_source = parts[0]
            field_name = parts[1] if len(parts) > 1 else base_source
            context_dict[f"{base_source}.{field_name}"] = series_obj
            context_dict[field_name] = series_obj
            context_dict[base_source] = series_obj
        else:
            context_dict[f"{source_name}.{source_name}"] = series_obj
            context_dict[source_name] = series_obj
        context_dict[key.source] = series_obj

    return context_dict


def resolve_source_from_context(expr: SourceRefNode, context: dict[str, Any]) -> Series[Any]:
    possible_keys = [
        f"{expr.source}.{expr.field}",
        expr.field,
    ]
    if expr.symbol and expr.timeframe:
        possible_keys.append(f"{expr.source}_{expr.symbol}_{expr.timeframe}_{expr.field}")
    if expr.symbol:
        possible_keys.append(f"{expr.symbol}_{expr.source}_{expr.field}")

    for key in possible_keys:
        if key in context:
            series = context[key]
            if isinstance(series, Series):
                return series

    raise MissingDataError(
        f"SourceExpression not found in context: {expr.source}.{expr.field}",
        source=expr.source,
        field=expr.field,
        symbol=expr.symbol,
        timeframe=expr.timeframe,
    )
