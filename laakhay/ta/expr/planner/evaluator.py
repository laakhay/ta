"""Evaluator using planned graphs for caching and dataset fan-out."""

from __future__ import annotations

from typing import Any

from ...core import Series
from ...core.dataset import Dataset
from ...core.series import align_series
from ...exceptions import MissingDataError
from ...registry.models import SeriesContext
from ..algebra.models import (
    SCALAR_SYMBOL,
    AggregateExpression,
    BinaryOp,
    FilterExpression,
    Literal,
    OperatorType,
    SourceExpression,
    TimeShiftExpression,
    UnaryOp,
)
from .types import PlanResult, SignalRequirements


class Evaluator:
    def __init__(self) -> None:
        # Per-node cache: (graph_hash, node_id, alignment, symbol, timeframe) -> output
        self._cache: dict[tuple, Any] = {}

    def evaluate(self, expr, data: Series[Any] | Dataset) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        plan = expr._ensure_plan()
        if isinstance(data, Series):
            context: dict[str, Series[Any]] = {"close": data}
            # Node-level caching is not performed for Series input
            return self._evaluate_graph(plan, context)
        if isinstance(data, Dataset):
            return self._evaluate_dataset(expr, plan, data)
        raise TypeError("Evaluator expects Series or Dataset")

    def _evaluate_dataset(self, expr, plan: PlanResult, dataset: Dataset) -> dict[tuple[str, str, str], Series[Any]]:
        if dataset.is_empty:
            return {}

        required_fields = _collect_required_field_names(plan.requirements)
        results: dict[tuple[str, str, str], Series[Any]] = {}
        unique_keys = {(key.symbol, key.timeframe) for key in dataset.keys}
        for symbol, timeframe in unique_keys:
            alignment_key = plan.alignment.cache_key()
            node_cache_key = (
                plan.graph_hash,
                plan.graph.root_id,
                alignment_key,
                symbol,
                timeframe,
            )
            if node_cache_key in self._cache:
                # Only retrieve the root node if all subnodes already cached
                results[(symbol, timeframe, "default")] = self._cache[node_cache_key]
                continue
            # Build context - try multi-source context first, fall back to standard
            try:
                # Try to build multi-source context for better support
                context = dataset.to_multisource_context(symbol=symbol, timeframe=timeframe)
                context_dict = {name: getattr(context, name) for name in context.available_series}
            except (ValueError, AttributeError):
                # Fall back to standard context building
                context = dataset.build_context(symbol, timeframe, required_fields)
                context_dict = {name: getattr(context, name) for name in context.available_series}

            # Also add source-specific keys for SourceExpression resolution
            # Add keys in format "source.field" for each series in the dataset
            for key, series_obj in dataset:
                if key.symbol == symbol and key.timeframe == timeframe:
                    if hasattr(series_obj, "to_series"):  # OHLCV
                        # Map "price" to "close" for OHLCV
                        field_mapping = {
                            "open": "open",
                            "high": "high",
                            "low": "low",
                            "close": "close",
                            "volume": "volume",
                            "price": "close",  # Map price to close
                        }
                        for field, ohlcv_field in field_mapping.items():
                            try:
                                field_series = series_obj.to_series(ohlcv_field)
                                context_dict[f"{key.source}.{field}"] = field_series
                                context_dict[field] = field_series  # Also add without source prefix
                            except (KeyError, AttributeError, ValueError):
                                pass
                    else:
                        # Regular series - handle source.field format for SourceExpression resolution
                        source_name = key.source
                        # If source contains underscore, it might be:
                        # 1. Exchange-qualified (e.g., "trades_binance") -> base_source = "trades"
                        # 2. Source_field format (e.g., "orderbook_imbalance") -> base_source = "orderbook", field = "imbalance"
                        if "_" in source_name:
                            parts = source_name.split("_", 1)  # Split only on first underscore
                            base_source = parts[0]
                            field_name = parts[1] if len(parts) > 1 else base_source

                            # Add with source.field format (e.g., "orderbook.imbalance")
                            context_dict[f"{base_source}.{field_name}"] = series_obj
                            # Also add with just field name for backward compatibility
                            context_dict[field_name] = series_obj
                            # Add with base source for backward compatibility
                            context_dict[base_source] = series_obj
                        else:
                            # Simple source name - add with source.source format and just source
                            context_dict[f"{source_name}.{source_name}"] = series_obj
                            context_dict[source_name] = series_obj
                        # Always add with full source name for backward compatibility
                        context_dict[key.source] = series_obj

            output = self._evaluate_graph(plan, context_dict, symbol, timeframe)
            results[(symbol, timeframe, "default")] = output
        return results

    def _evaluate_graph(
        self,
        plan: PlanResult,
        context: dict[str, Any],
        symbol: str = None,
        timeframe: str = None,
    ) -> Any:
        graph = plan.graph
        order = plan.node_order
        node_outputs: dict[int, Any] = {}
        alignment = plan.alignment
        alignment_args = dict(
            how=alignment.how,
            fill=alignment.fill,
            left_fill_value=alignment.left_fill_value,
            right_fill_value=alignment.right_fill_value,
        )
        for node_id in order:
            node = graph.nodes[node_id]
            children_outputs = [node_outputs[child_id] for child_id in node.children]
            cache_key = (
                (plan.graph_hash, node_id, alignment.cache_key(), symbol, timeframe)
                if symbol is not None and timeframe is not None
                else None
            )

            if cache_key is not None and cache_key in self._cache:
                out = self._cache[cache_key]
            else:
                out = self._eval_node(node, children_outputs, context, alignment_args)
                if cache_key is not None:
                    self._cache[cache_key] = out
            node_outputs[node_id] = out
        return node_outputs[graph.root_id]

    def _eval_node(self, node, children_outputs, context, alignment_args):
        n = node.node
        # BinaryOp central alignment
        if isinstance(n, BinaryOp):
            arithmetic_ops = {
                OperatorType.ADD,
                OperatorType.SUB,
                OperatorType.MUL,
                OperatorType.DIV,
                OperatorType.MOD,
                OperatorType.POW,
            }
            comparison_ops = {
                OperatorType.EQ,
                OperatorType.NE,
                OperatorType.LT,
                OperatorType.LE,
                OperatorType.GT,
                OperatorType.GE,
            }
            # If operator is a Series operation, align both children before passing to op logic
            if n.operator in arithmetic_ops | comparison_ops:
                left, right = children_outputs[0], children_outputs[1]
                # Ensure both operands are Series objects (convert scalars if needed)
                from ..algebra.models import _make_scalar_series

                if not isinstance(left, Series):
                    left = _make_scalar_series(left)
                if not isinstance(right, Series):
                    right = _make_scalar_series(right)

                if isinstance(left, Series) and isinstance(right, Series):
                    left_is_scalar = left.symbol == SCALAR_SYMBOL
                    right_is_scalar = right.symbol == SCALAR_SYMBOL
                    if not (left_is_scalar or right_is_scalar):
                        left, right = align_series(
                            left,
                            right,
                            **alignment_args,
                            symbol=left.symbol,
                            timeframe=left.timeframe,
                        )
                return n.evaluate_aligned(left, right)
            # Otherwise, fallback to default logic (e.g. logical)
            return n.evaluate(context)
        elif isinstance(n, UnaryOp):
            return n.evaluate(context)
        elif isinstance(n, Literal):
            result = n.evaluate(context)
            # If result is a scalar Series, extract the scalar value for test compatibility
            if isinstance(result, Series) and result.symbol == SCALAR_SYMBOL and len(result) == 1:
                return result.values[0]
            return result
        elif isinstance(n, SourceExpression):
            return self._evaluate_source_expression(n, context)
        elif isinstance(n, FilterExpression):
            # Evaluate child expressions (series and condition)
            # Children should be in children_outputs if graph was built correctly
            if len(children_outputs) >= 2:
                series_expr = children_outputs[0]
                condition_expr = children_outputs[1]
            else:
                # Fallback: evaluate directly from node
                series_expr = n.series.evaluate(context)
                condition_expr = n.condition.evaluate(context)
            return self._evaluate_filter_expression(series_expr, condition_expr)
        elif isinstance(n, AggregateExpression):
            # Evaluate child expression (series)
            if len(children_outputs) >= 1:
                series_expr = children_outputs[0]
            else:
                # Fallback: evaluate directly from node
                series_expr = n.series.evaluate(context)
            return self._evaluate_aggregate_expression(series_expr, n.operation, n.field)
        elif isinstance(n, TimeShiftExpression):
            # Evaluate child expression (series)
            if len(children_outputs) >= 1:
                series_expr = children_outputs[0]
            else:
                # Fallback: evaluate directly from node
                series_expr = n.series.evaluate(context)
            return self._evaluate_time_shift_expression(series_expr, n.shift, n.operation)
        elif hasattr(n, "__class__") and n.__class__.__name__ == "IndicatorNode":
            # If indicator has input_series and it was evaluated as a child, use that result
            if hasattr(n, "input_series") and n.input_series is not None and len(children_outputs) >= 1:
                # Use the pre-evaluated input_series from children
                input_series_result = children_outputs[0]
                # Create context with the input series as 'close'
                ctx = {"close": input_series_result}
                # Evaluate the indicator with this context
                if n.name not in n._registry._indicators:
                    raise ValueError(f"Indicator '{n.name}' not found in registry")
                indicator_func = n._registry._indicators[n.name]
                params_without_input = {k: v for k, v in n.params.items() if k != "input_series"}
                return indicator_func(SeriesContext(**ctx), **params_without_input)
            # Otherwise, use standard evaluation (which will evaluate input_series if present)
            return n.run(context)
        else:
            raise NotImplementedError(f"Unsupported node type: {type(n)}")

    def _evaluate_source_expression(self, expr: SourceExpression, context: dict[str, Any]) -> Series[Any]:
        """Evaluate SourceExpression by resolving series from context.

        Args:
            expr: SourceExpression to evaluate
            context: Context dictionary containing series

        Returns:
            Series from the context

        Raises:
            ValueError: If the required series is not found in context
        """
        # Build context key based on source expression attributes
        # Try multiple key formats for flexibility
        possible_keys = []

        # Format: source.field (e.g., "trades.volume")
        possible_keys.append(f"{expr.source}.{expr.field}")

        # Format: source_symbol_timeframe_field (e.g., "trades_BTC_1h_volume")
        if expr.symbol and expr.timeframe:
            possible_keys.append(f"{expr.source}_{expr.symbol}_{expr.timeframe}_{expr.field}")

        # Format: symbol_source_field (e.g., "BTC_trades_volume")
        if expr.symbol:
            possible_keys.append(f"{expr.symbol}_{expr.source}_{expr.field}")

        # Format: just the field name (e.g., "volume")
        possible_keys.append(expr.field)

        # Try each possible key
        for key in possible_keys:
            if key in context:
                series = context[key]
                if isinstance(series, Series):
                    return series

        # If not found, raise MissingDataError with context
        raise MissingDataError(
            f"SourceExpression not found in context: {expr.source}.{expr.field}",
            source=expr.source,
            field=expr.field,
            symbol=expr.symbol,
            timeframe=expr.timeframe,
        )

    def _evaluate_filter_expression(self, series: Series[Any], condition: Series[bool]) -> Series[Any]:
        """Evaluate FilterExpression by filtering series based on condition.

        Args:
            series: Series to filter
            condition: Boolean series indicating which elements to keep

        Returns:
            Filtered series
        """
        if not isinstance(series, Series):
            raise TypeError(f"Expected Series, got {type(series)}")
        if not isinstance(condition, Series):
            raise TypeError(f"Expected Series[bool], got {type(condition)}")

        return series.filter(condition)

    def _evaluate_aggregate_expression(self, series: Series[Any], operation: str, field: str | None) -> Series[Any]:
        """Evaluate AggregateExpression by applying aggregation operation.

        Args:
            series: Series to aggregate
            operation: Aggregation operation ('count', 'sum', 'avg', 'max', 'min')
            field: Optional field name (for future use with structured data)

        Returns:
            Aggregated series (typically single value)

        Raises:
            ValueError: If operation is not supported
        """
        if not isinstance(series, Series):
            raise TypeError(f"Expected Series, got {type(series)}")

        if operation == "count":
            return series.count()
        elif operation == "sum":
            return series.sum(field)
        elif operation == "avg":
            return series.avg(field)
        elif operation == "max":
            return series.max(field)
        elif operation == "min":
            return series.min(field)
        else:
            raise ValueError(f"Unknown aggregation operation: {operation}")

    def _evaluate_time_shift_expression(self, series: Series[Any], shift: str, operation: str | None) -> Series[Any]:
        """Evaluate TimeShiftExpression by applying time shift and optional operation.

        Args:
            series: Base series to shift
            shift: Shift specification (e.g., "24h_ago", "1h", "1")
            operation: Optional operation ('change', 'change_pct', None for just shift)

        Returns:
            Shifted or transformed series

        Raises:
            ValueError: If shift format is invalid
        """
        if not isinstance(series, Series):
            raise TypeError(f"Expected Series, got {type(series)}")

        # Parse shift string to extract periods
        # Support formats: "24h_ago", "1h", "1", "24h"
        periods = 1  # default
        if shift.endswith("_ago"):
            # Format: "24h_ago" -> extract number and convert to periods
            shift_part = shift[:-4]  # Remove "_ago"
            if shift_part.endswith("h"):
                hours = int(shift_part[:-1])
                # For now, assume 1 period per hour (this should be based on timeframe)
                periods = hours
            elif shift_part.endswith("m"):
                minutes = int(shift_part[:-1])
                periods = minutes // 60  # Convert to hours (rough approximation)
            else:
                try:
                    periods = int(shift_part)
                except ValueError:
                    raise ValueError(f"Invalid shift format: {shift}")
        elif shift.endswith("h"):
            hours = int(shift[:-1])
            periods = hours
        elif shift.endswith("m"):
            minutes = int(shift[:-1])
            periods = minutes // 60
        else:
            try:
                periods = int(shift)
            except ValueError:
                raise ValueError(f"Invalid shift format: {shift}")

        # Apply shift
        shifted = series.shift(-periods)  # Negative for "ago" (looking back)

        # Apply operation if specified
        if operation == "change":
            return series.change(periods)
        elif operation == "change_pct":
            return series.change_pct(periods)
        elif operation is None:
            return shifted
        else:
            raise ValueError(f"Unknown time shift operation: {operation}")


def _collect_required_field_names(requirements: SignalRequirements) -> list[str]:
    names = {field.name for field in requirements.fields if field.name}
    if not names:
        names = {"close"}
    return sorted(names)
