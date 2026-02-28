"""Output serialization utilities."""

from __future__ import annotations

from typing import Any

from ..core import Series
from .utils import jsonify_value, to_epoch_seconds, to_float


class OutputSerializer:
    """Serializes indicator results to structured formats (JSON-compatible)."""

    def __init__(self) -> None:
        """Initialize output serializer."""
        pass

    def serialize_series(
        self, series: Series[Any], output_name: str | None = None
    ) -> dict[str, list[dict[str, float]]]:
        """
        Serialize a Series to JSON-compatible format.

        Args:
            series: Series to serialize
            output_name: Name for the output (defaults to series symbol/timeframe)

        Returns:
            Dictionary mapping output name to list of points
            Each point has 'time' (epoch seconds) and 'value' (float) keys
        """
        outputs: dict[str, list[dict[str, float]]] = {}
        label = output_name or f"{series.symbol}_{series.timeframe}"

        points: list[dict[str, float]] = []
        mask = series.availability_mask
        for idx, (ts, val) in enumerate(zip(series.timestamps, series.values, strict=False)):
            if mask and not mask[idx]:
                continue
            ts_value = to_epoch_seconds(ts)
            val_float = to_float(val)
            if ts_value is None or val_float is None:
                continue
            points.append({"time": ts_value, "value": val_float})
        if points:
            outputs[label] = points
        return outputs

    def serialize_result(
        self,
        result: Any,
        output_names: tuple[str, ...] | None = None,
        default_name: str = "result",
    ) -> tuple[dict[str, list[dict[str, float]]], dict[str, Any]]:
        """
        Serialize indicator result to structured format.

        Handles Series, dict, list/tuple, and scalar values.

        Args:
            result: Indicator result (Series, dict, list, tuple, or scalar)
            output_names: Tuple of output names for tuple/list results
            default_name: Default name for scalar results

        Returns:
            Tuple of (outputs dict, metadata dict)
            - outputs: Maps output names to lists of time/value points
            - metadata: Maps names to scalar/metadata values
        """
        outputs: dict[str, list[dict[str, float]]] = {}
        meta: dict[str, Any] = {}

        def handle_series(series: Series[Any], label: str) -> None:
            """Handle Series output."""
            points: list[dict[str, float]] = []
            mask = series.availability_mask
            for idx, (ts, val) in enumerate(zip(series.timestamps, series.values, strict=False)):
                if mask and not mask[idx]:
                    continue
                ts_value = to_epoch_seconds(ts)
                val_float = to_float(val)
                if ts_value is None or val_float is None:
                    continue
                points.append({"time": ts_value, "value": val_float})
            if points:
                outputs[label] = points

        def walk(node: Any, prefix: str | None = None, index: int | None = None) -> None:
            """Recursively walk result structure."""
            if isinstance(node, Series):
                label = prefix or default_name
                handle_series(node, label)
                return
            if isinstance(node, dict):
                for key, val in node.items():
                    sub_prefix = f"{prefix}.{key}" if prefix else key
                    walk(val, sub_prefix)
                return
            if isinstance(node, list | tuple):
                aliases = output_names or ()
                for idx, item in enumerate(node):
                    label = aliases[idx] if idx < len(aliases) else (f"{prefix}_{idx}" if prefix else f"value_{idx}")
                    walk(item, label, idx)
                return
            label = prefix or default_name
            meta[label] = jsonify_value(node)

        walk(result)
        return outputs, meta


def serialize_series(series: Series[Any], output_name: str | None = None) -> dict[str, list[dict[str, float]]]:
    """Convenience function to serialize a Series.

    Args:
        series: Series to serialize
        output_name: Name for the output

    Returns:
        Dictionary mapping output name to list of points
    """
    serializer = OutputSerializer()
    return serializer.serialize_series(series, output_name)
