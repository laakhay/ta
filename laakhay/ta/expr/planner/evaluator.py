"""Evaluator using planned graphs for caching and dataset fan-out."""

from __future__ import annotations

from typing import Any

from ...core import Series
from ...core.dataset import Dataset
from ...core.series import align_series
from ...exceptions import MissingDataError
from ...registry.models import SeriesContext
from ..ir.nodes import (
    CanonicalExpression, LiteralNode, CallNode, SourceRefNode,
    BinaryOpNode, UnaryOpNode, FilterNode, AggregateNode,
    TimeShiftNode, SCALAR_SYMBOL
)
from .types import PlanResult, SignalRequirements


class Evaluator:
    def __init__(self) -> None:
        # Per-node cache: (graph_hash, node_id, alignment, symbol, timeframe) -> output
        self._cache: dict[tuple, Any] = {}

    def evaluate(
        self,
        expr,
        data: Series[Any] | Dataset | dict[str, Series[Any]],
        return_all_outputs: bool = False,
    ) -> Series[Any] | dict[tuple[str, str, str], Series[Any]] | tuple[Any, dict[int, Any]]:
        plan = expr._ensure_plan()
        if isinstance(data, Series):
            context: dict[str, Series[Any]] = {"close": data}
            # Node-level caching is not performed for Series input
            return self._evaluate_graph(plan, context, return_all_outputs=return_all_outputs)
        if isinstance(data, dict):
            return self._evaluate_graph(plan, data, return_all_outputs=return_all_outputs)
        if isinstance(data, Dataset):
            return self._evaluate_dataset(expr, plan, data, return_all_outputs=return_all_outputs)
        raise TypeError(f"Evaluator expects Series, Dataset, or dict, got {type(data)}")

    def _evaluate_dataset(
        self,
        expr,
        plan: PlanResult,
        dataset: Dataset,
        return_all_outputs: bool = False,
    ) -> dict[tuple[str, str, str], Series[Any]] | tuple[dict[tuple[str, str, str], Series[Any]], dict[int, Any]]:
        if dataset.is_empty:
            return {}

        required_fields = _collect_required_field_names(plan.requirements)
        results: dict[tuple[str, str, str], Series[Any]] = {}
        all_node_outputs: dict[int, Any] = {}
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
            if node_cache_key in self._cache and not return_all_outputs:
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

            if return_all_outputs:
                output, node_outputs = self._evaluate_graph(
                    plan, context_dict, symbol, timeframe, return_all_outputs=True
                )
                all_node_outputs.update(node_outputs)
            else:
                output = self._evaluate_graph(plan, context_dict, symbol, timeframe)
            results[(symbol, timeframe, "default")] = output

        if return_all_outputs:
            return results, all_node_outputs
        return results

    def _evaluate_graph(
        self,
        plan: PlanResult,
        context: dict[str, Any],
        symbol: str = None,
        timeframe: str = None,
        return_all_outputs: bool = False,
    ) -> Any | tuple[Any, dict[int, Any]]:
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

        if return_all_outputs:
            return node_outputs[graph.root_id], node_outputs
        return node_outputs[graph.root_id]

    def _eval_node(self, node, children_outputs, context, alignment_args):
        n = node.node
        if isinstance(n, BinaryOpNode):
            arithmetic_ops = {"add", "sub", "mul", "div", "mod", "pow"}
            comparison_ops = {"eq", "neq", "lt", "lte", "gt", "gte"}
            logical_ops = {"and", "or"}
            
            left, right = children_outputs[0], children_outputs[1]
            from ..algebra.scalar_helpers import _make_scalar_series
            
            if not isinstance(left, Series):
                left = _make_scalar_series(left)
            if not isinstance(right, Series):
                right = _make_scalar_series(right)
                
            left_aligned, right_aligned = left, right
            if n.operator in arithmetic_ops | comparison_ops | logical_ops:
                left_is_scalar = left.symbol == SCALAR_SYMBOL
                right_is_scalar = right.symbol == SCALAR_SYMBOL
                if not (left_is_scalar or right_is_scalar):
                    if left.symbol != right.symbol or left.timeframe != right.timeframe:
                        raise ValueError("mismatched metadata")
                    left_aligned, right_aligned = align_series(
                        left, right,
                        **alignment_args,
                        symbol=left.symbol,
                        timeframe=left.timeframe,
                    )
                elif left_is_scalar and not right_is_scalar:
                    from ..algebra.scalar_helpers import _broadcast_scalar_series
                    left_aligned = _broadcast_scalar_series(left_aligned, right_aligned)
                elif right_is_scalar and not left_is_scalar:
                    from ..algebra.scalar_helpers import _broadcast_scalar_series
                    right_aligned = _broadcast_scalar_series(right_aligned, left_aligned)
            
            op = n.operator
            if op == "add": return left_aligned + right_aligned
            elif op == "sub": return left_aligned - right_aligned
            elif op == "mul": return left_aligned * right_aligned
            elif op == "div": return left_aligned / right_aligned
            elif op == "mod": return left_aligned % right_aligned
            elif op == "pow": return left_aligned ** right_aligned
            elif op == "eq": return self._comparison_series(left_aligned, right_aligned, lambda a, b: a == b)
            elif op == "neq": return self._comparison_series(left_aligned, right_aligned, lambda a, b: a != b)
            elif op == "lt": return self._comparison_series(left_aligned, right_aligned, lambda a, b: a < b)
            elif op == "lte": return self._comparison_series(left_aligned, right_aligned, lambda a, b: a <= b)
            elif op == "gt": return self._comparison_series(left_aligned, right_aligned, lambda a, b: a > b)
            elif op == "gte": return self._comparison_series(left_aligned, right_aligned, lambda a, b: a >= b)
            elif op in {"and", "or"}:
                from decimal import Decimal
                def _truthy(v: Any) -> bool:
                    if isinstance(v, bool): return v
                    if isinstance(v, (int, float, Decimal)): return bool(Decimal(str(v)))
                    try: return bool(Decimal(str(v)))
                    except Exception: return bool(v)
                
                values = tuple(
                    _truthy(lv) and _truthy(rv) if op == "and" else _truthy(lv) or _truthy(rv)
                    for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False)
                )
                return Series[bool](
                    timestamps=left_aligned.timestamps,
                    values=values,
                    symbol=left_aligned.symbol,
                    timeframe=left_aligned.timeframe,
                )
            raise NotImplementedError(f"operator {op} not supported")
            
        elif isinstance(n, UnaryOpNode):
            operand = children_outputs[0]
            if not isinstance(operand, Series):
                from ..algebra.scalar_helpers import _make_scalar_series
                operand = _make_scalar_series(operand)
            op = n.operator
            if op == "neg": return -operand
            elif op == "pos": return operand
            elif op == "not":
                from decimal import Decimal
                def _truthy(v: Any) -> bool:
                    if isinstance(v, bool): return v
                    if isinstance(v, (int, float, Decimal)): return bool(Decimal(str(v)))
                    try: return bool(Decimal(str(v)))
                    except Exception: return bool(v)
                return Series[bool](
                    timestamps=operand.timestamps,
                    values=tuple(not _truthy(v) for v in operand.values),
                    symbol=operand.symbol,
                    timeframe=operand.timeframe,
                )
            raise NotImplementedError(f"Unary operator {op} not implemented")
            
        elif isinstance(n, LiteralNode):
            if isinstance(n.value, Series) and n.value.symbol == SCALAR_SYMBOL and len(n.value) == 1:
                return n.value.values[0]
            if isinstance(n.value, Series):
                return n.value
            return n.value
            
        elif isinstance(n, SourceRefNode):
            return self._evaluate_source_expression(n, context)
            
        elif isinstance(n, FilterNode):
            series_expr = children_outputs[0] if len(children_outputs) >= 1 else None
            condition_expr = children_outputs[1] if len(children_outputs) >= 2 else None
            return self._evaluate_filter_expression(series_expr, condition_expr)
            
        elif isinstance(n, AggregateNode):
            series_expr = children_outputs[0] if len(children_outputs) >= 1 else None
            return self._evaluate_aggregate_expression(series_expr, n.operation, n.field)
            
        elif isinstance(n, TimeShiftNode):
            series_expr = children_outputs[0] if len(children_outputs) >= 1 else None
            return self._evaluate_time_shift_expression(series_expr, n.shift, n.operation)
            
        elif isinstance(n, CallNode):
            from ...registry.registry import get_global_registry
            registry = get_global_registry()
            
            if n.name not in registry._indicators:
                raise ValueError(f"Indicator '{n.name}' not found in registry")
            indicator_func = registry._indicators[n.name]

            # Map evaluated children back to args and kwargs
            eval_args = children_outputs[:len(n.args)]
            eval_kwargs = n.kwargs.copy()
            
            kwarg_outputs = children_outputs[len(n.args):]
            for key, val in zip(sorted(n.kwargs.keys()), kwarg_outputs):
                eval_kwargs[key] = val

            if n.input_expr is not None and len(eval_args) > 0:
                input_series_result = eval_args[0]
                remaining_args = eval_args[1:]

                if isinstance(input_series_result, Series):
                    return indicator_func(SeriesContext(close=input_series_result), *remaining_args, **eval_kwargs)
                
                base_ctx = SeriesContext(**context)
                return indicator_func(base_ctx, input_series_result, *remaining_args, **eval_kwargs)

            return indicator_func(SeriesContext(**context), *eval_args, **eval_kwargs)
            
        else:
            raise NotImplementedError(f"Unsupported node type: {type(n)}")

    def _comparison_series(self, left: Series[Any], right: Series[Any], compare) -> Series[bool]:
        result_values = tuple(
            bool(compare(lv, rv)) for lv, rv in zip(left.values, right.values, strict=False)
        )
        return Series[bool](
            timestamps=left.timestamps,
            values=result_values,
            symbol=left.symbol,
            timeframe=left.timeframe,
        )

    def _evaluate_source_expression(self, expr: SourceRefNode, context: dict[str, Any]) -> Series[Any]:
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
    names = {req.field for req in requirements.data_requirements if req.field}
    if not names:
        names = {"close"}
    return sorted(names)
