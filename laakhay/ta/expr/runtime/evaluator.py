"""Runtime evaluator for expression graphs with Dataset integration and caching.

This evaluator walks PlanResult graphs, resolves SourceExpressions via Dataset
helpers, and executes filters/aggregations/time shifts using Series primitives.
Includes caching per (symbol, timeframe, source) to avoid recomputing series.
"""

from __future__ import annotations

from typing import Any

from ...core import Series
from ...core.dataset import Dataset
from ...core.series import align_series
from ...exceptions import MissingDataError
from ...registry.models import SeriesContext
from ..ir.nodes import (
    SCALAR_SYMBOL,
    AggregateNode,
    BinaryOpNode,
    CallNode,
    FilterNode,
    LiteralNode,
    SourceRefNode,
    TimeShiftNode,
    UnaryOpNode,
)
from ..planner.types import PlanResult


class RuntimeEvaluator:
    """Runtime evaluator that walks PlanResult graphs with Dataset integration.

    Features:
    - Walks expression graphs in topological order
    - Resolves SourceExpressions via Dataset helpers
    - Executes filters/aggregations/time shifts using Series primitives
    - Caches results per (symbol, timeframe, source) dataset
    - Handles multi-source data (OHLCV, trades, orderbook, liquidations)
    """

    def __init__(self) -> None:
        """Initialize runtime evaluator with empty cache."""
        # Cache key: (graph_hash, node_id, symbol, timeframe, source) -> Series
        self._cache: dict[tuple[str, int, str, str, str], Series[Any]] = {}

    def evaluate(
        self,
        plan: PlanResult,
        dataset: Dataset,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        """Evaluate a planned expression against a dataset.

        Args:
            plan: PlanResult containing the expression graph and requirements
            dataset: Dataset containing series data
            symbol: Optional symbol filter (if None, evaluates for all symbols)
            timeframe: Optional timeframe filter (if None, evaluates for all timeframes)

        Returns:
            Series if symbol/timeframe specified, otherwise dict mapping
            (symbol, timeframe, source) tuples to Series results
        """
        if dataset.is_empty:
            return (
                {}
                if symbol is None
                else Series[Any](timestamps=(), values=(), symbol=symbol or "", timeframe=timeframe or "")
            )

        if symbol is not None and timeframe is not None:
            # Single symbol/timeframe evaluation
            return self._evaluate_single(plan, dataset, symbol, timeframe)

        # Multi-symbol/timeframe evaluation
        return self._evaluate_multi(plan, dataset)

    def _evaluate_single(
        self,
        plan: PlanResult,
        dataset: Dataset,
        symbol: str,
        timeframe: str,
    ) -> Series[Any]:
        """Evaluate expression for a single symbol/timeframe."""
        context = self._build_context(plan, dataset, symbol, timeframe)
        return self._evaluate_graph(plan, context, symbol, timeframe)

    def _evaluate_multi(
        self,
        plan: PlanResult,
        dataset: Dataset,
    ) -> dict[tuple[str, str, str], Series[Any]]:
        """Evaluate expression for all symbol/timeframe combinations."""
        results: dict[tuple[str, str, str], Series[Any]] = {}
        unique_keys = {(key.symbol, key.timeframe) for key in dataset.keys}

        for symbol, timeframe in unique_keys:
            context = self._build_context(plan, dataset, symbol, timeframe)
            output = self._evaluate_graph(plan, context, symbol, timeframe)
            results[(symbol, timeframe, "default")] = output

        return results

    def _build_context(
        self,
        plan: PlanResult,
        dataset: Dataset,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Series[Any]]:
        """Build evaluation context from dataset for given symbol/timeframe.

        Resolves all required data sources and fields, creating a context
        dictionary that maps field names to Series objects.
        """
        context: dict[str, Series[Any]] = {}

        # Try multi-source context first
        try:
            multisource_ctx = dataset.to_multisource_context(symbol=symbol, timeframe=timeframe)
            for name in multisource_ctx.available_series:
                context[name] = getattr(multisource_ctx, name)
        except (ValueError, AttributeError):
            # Fall back to standard context
            required_fields = [field.name for field in plan.requirements.fields]
            standard_ctx = dataset.build_context(symbol, timeframe, required_fields)
            for name in standard_ctx.available_series:
                context[name] = getattr(standard_ctx, name)

        # Add source-specific keys for SourceExpression resolution
        # Format: "source.field" for each series in the dataset
        for key, series_obj in dataset:
            if key.symbol == symbol and key.timeframe == timeframe:
                if hasattr(series_obj, "to_series"):  # OHLCV
                    # Map OHLCV fields
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
                            context[f"{key.source}.{field}"] = field_series
                            context[field] = field_series  # Also add without source prefix
                        except (KeyError, AttributeError, ValueError):
                            pass
                else:
                    # Regular series - add with source prefix
                    context[f"{key.source}.{key.source}"] = series_obj
                    context[key.source] = series_obj

        return context

    def _evaluate_graph(
        self,
        plan: PlanResult,
        context: dict[str, Series[Any]],
        symbol: str,
        timeframe: str,
    ) -> Series[Any]:
        """Evaluate expression graph in topological order.

        Walks the graph following node_order, evaluating each node
        after its dependencies have been evaluated.
        """
        graph = plan.graph
        order = plan.node_order
        node_outputs: dict[int, Series[Any]] = {}
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

            # Check cache
            cache_key = (
                plan.graph_hash,
                node_id,
                symbol,
                timeframe,
                "default",  # source
            )
            if cache_key in self._cache:
                out = self._cache[cache_key]
            else:
                out = self._eval_node(node, children_outputs, context, alignment_args, symbol, timeframe)
                self._cache[cache_key] = out

            node_outputs[node_id] = out

        return node_outputs[graph.root_id]

    def _eval_node(
        self,
        node: Any,
        children_outputs: list[Series[Any]],
        context: dict[str, Series[Any]],
        alignment_args: dict[str, Any],
        symbol: str,
        timeframe: str,
    ) -> Series[Any]:
        """Evaluate a single node in the expression graph."""
        n = node.node

        if isinstance(n, BinaryOpNode):
            return self._eval_binary_op(n, children_outputs, alignment_args)

        if isinstance(n, UnaryOpNode):
            return self._eval_unary_op(n, children_outputs)

        if isinstance(n, LiteralNode):
            return self._eval_literal_node(n, context)

        if isinstance(n, SourceRefNode):
            return self._eval_source_expression(n, context, symbol, timeframe)

        if isinstance(n, FilterNode):
            return self._eval_filter_expression(n, children_outputs, context)

        if isinstance(n, AggregateNode):
            return self._eval_aggregate_expression(n, children_outputs, context)

        if isinstance(n, TimeShiftNode):
            return self._eval_time_shift_expression(n, children_outputs, context)

        if isinstance(n, CallNode):
            return self._eval_indicator_node(n, children_outputs, context)

        from ...exceptions import EvaluationError

        raise EvaluationError(
            f"Unsupported node type: {type(n)}",
            node_type=type(n).__name__,
            context={"node": str(n)},
        )

    def _eval_binary_op(
        self,
        n: BinaryOpNode,
        children_outputs: list[Series[Any]],
        alignment_args: dict[str, Any],
    ) -> Series[Any]:
        """Evaluate binary operation with alignment."""
        if len(children_outputs) < 2:
            raise ValueError(f"Binary operation requires 2 operands, got {len(children_outputs)}")

        left, right = children_outputs[0], children_outputs[1]

        # Ensure both are Series objects
        from ..algebra.scalar_helpers import _make_scalar_series

        if not isinstance(left, Series):
            left = _make_scalar_series(left)
        if not isinstance(right, Series):
            right = _make_scalar_series(right)

        # Align series if needed
        left_aligned, right_aligned = left, right
        arithmetic_ops = {"add", "sub", "mul", "div", "mod", "pow"}
        comparison_ops = {"eq", "neq", "lt", "lte", "gt", "gte"}
        logical_ops = {"and", "or"}

        if n.operator in arithmetic_ops | comparison_ops | logical_ops:
            left_is_scalar = left.symbol == SCALAR_SYMBOL
            right_is_scalar = right.symbol == SCALAR_SYMBOL
            if not (left_is_scalar or right_is_scalar):
                if left.symbol != right.symbol or left.timeframe != right.timeframe:
                    raise ValueError("mismatched metadata")
                left_aligned, right_aligned = align_series(
                    left,
                    right,
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
        if op == "add":
            return left_aligned + right_aligned
        elif op == "sub":
            return left_aligned - right_aligned
        elif op == "mul":
            return left_aligned * right_aligned
        elif op == "div":
            return left_aligned / right_aligned
        elif op == "mod":
            return left_aligned % right_aligned
        elif op == "pow":
            return left_aligned**right_aligned
        elif op == "eq":
            return self._comparison_series(left_aligned, right_aligned, lambda a, b: a == b)
        elif op == "neq":
            return self._comparison_series(left_aligned, right_aligned, lambda a, b: a != b)
        elif op == "lt":
            return self._comparison_series(left_aligned, right_aligned, lambda a, b: a < b)
        elif op == "lte":
            return self._comparison_series(left_aligned, right_aligned, lambda a, b: a <= b)
        elif op == "gt":
            return self._comparison_series(left_aligned, right_aligned, lambda a, b: a > b)
        elif op == "gte":
            return self._comparison_series(left_aligned, right_aligned, lambda a, b: a >= b)
        elif op in {"and", "or"}:
            from decimal import Decimal

            def _truthy(v: Any) -> bool:
                if isinstance(v, bool):
                    return v
                if isinstance(v, (int, float, Decimal)):
                    return bool(Decimal(str(v)))
                try:
                    return bool(Decimal(str(v)))
                except Exception:
                    return bool(v)

            values = tuple(
                (_truthy(lv) and _truthy(rv)) if op == "and" else (_truthy(lv) or _truthy(rv))
                for lv, rv in zip(left_aligned.values, right_aligned.values, strict=False)
            )
            return Series[bool](
                timestamps=left_aligned.timestamps,
                values=values,
                symbol=left_aligned.symbol,
                timeframe=left_aligned.timeframe,
            )
        raise NotImplementedError(f"operator {op} not supported")

    def _comparison_series(self, left: Series[Any], right: Series[Any], compare) -> Series[bool]:
        # Debugging print
        print(f"\n_comparison_series left len: {len(left.timestamps)} vs {len(left.values)}")
        print(f"_comparison_series right len: {len(right.timestamps)} vs {len(right.values)}")
        result_values = tuple(bool(compare(lv, rv)) for lv, rv in zip(left.values, right.values, strict=False))
        return Series[bool](
            timestamps=left.timestamps,
            values=result_values,
            symbol=left.symbol,
            timeframe=left.timeframe,
        )

    def _eval_unary_op(self, n: UnaryOpNode, children_outputs: list[Series[Any]]) -> Series[Any]:
        operand = children_outputs[0]
        if not isinstance(operand, Series):
            from ..algebra.scalar_helpers import _make_scalar_series

            operand = _make_scalar_series(operand)
        op = n.operator
        if op == "neg":
            return -operand
        elif op == "pos":
            return operand
        elif op == "not":
            from decimal import Decimal

            def _truthy(v: Any) -> bool:
                if isinstance(v, bool):
                    return v
                if isinstance(v, (int, float, Decimal)):
                    return bool(Decimal(str(v)))
                try:
                    return bool(Decimal(str(v)))
                except Exception:
                    return bool(v)

            return Series[bool](
                timestamps=operand.timestamps,
                values=tuple(not _truthy(v) for v in operand.values),
                symbol=operand.symbol,
                timeframe=operand.timeframe,
            )
        raise NotImplementedError(f"Unary operator {op} not implemented")

    def _eval_literal_node(self, n: LiteralNode, context: dict[str, Series[Any]]) -> Any:
        if isinstance(n.value, Series) and n.value.symbol == SCALAR_SYMBOL and len(n.value) == 1:
            return n.value.values[0]
        if isinstance(n.value, Series):
            return n.value
        return n.value

    def _eval_source_expression(
        self,
        expr: SourceRefNode,
        context: dict[str, Series[Any]],
        symbol: str,
        timeframe: str,
    ) -> Series[Any]:
        """Resolve SourceExpression from context.

        First tries to use Dataset.resolve() if dataset is available in context,
        otherwise falls back to context dictionary lookup.
        """
        # Try context dictionary first (for backwards compatibility)
        possible_keys = []

        # Format: source.field (e.g., "trades.volume")
        possible_keys.append(f"{expr.source}.{expr.field}")

        # Format: source_symbol_timeframe_field
        if expr.symbol and expr.timeframe:
            possible_keys.append(f"{expr.source}_{expr.symbol}_{expr.timeframe}_{expr.field}")

        # Format: symbol_source_field
        if expr.symbol:
            possible_keys.append(f"{expr.symbol}_{expr.source}_{expr.field}")

        # Format: just the field name
        possible_keys.append(expr.field)

        # Try each possible key
        for key in possible_keys:
            if key in context:
                series = context[key]
                if isinstance(series, Series):
                    return series

        # If not found in context dict, try to get dataset from context and use resolve()
        # This is a fallback for when context doesn't have the pre-resolved series
        # In most cases, the series should already be in the context dict from to_multisource_context()
        raise MissingDataError(
            f"SourceExpression not found in context: {expr.source}.{expr.field}",
            source=expr.source,
            field=expr.field,
            symbol=expr.symbol or symbol,
            timeframe=expr.timeframe or timeframe,
        )

    def _eval_filter_expression(
        self,
        expr: FilterNode,
        children_outputs: list[Series[Any]],
        context: dict[str, Series[Any]],
    ) -> Series[Any]:
        """Evaluate FilterExpression using Series.filter."""
        if len(children_outputs) >= 2:
            series_expr = children_outputs[0]
            condition_expr = children_outputs[1]
        else:
            raise ValueError("FilterNode requires 2 evaluated children")

        from ...exceptions import EvaluationError

        if not isinstance(series_expr, Series):
            raise EvaluationError(
                f"Expected Series for filter, got {type(series_expr)}",
                node_type="FilterExpression",
                context={"series_type": type(series_expr).__name__},
            )
        if not isinstance(condition_expr, Series):
            raise EvaluationError(
                f"Expected Series[bool] for filter condition, got {type(condition_expr)}",
                node_type="FilterExpression",
                context={"condition_type": type(condition_expr).__name__},
            )

        return series_expr.filter(condition_expr)

    def _eval_aggregate_expression(
        self,
        expr: AggregateNode,
        children_outputs: list[Series[Any]],
        context: dict[str, Series[Any]],
    ) -> Series[Any]:
        """Evaluate AggregateExpression using Series aggregation methods."""
        if len(children_outputs) >= 1:
            series_expr = children_outputs[0]
        else:
            raise ValueError("AggregateNode requires 1 evaluated child")

        from ...exceptions import EvaluationError

        if not isinstance(series_expr, Series):
            raise EvaluationError(
                f"Expected Series for aggregation, got {type(series_expr)}",
                node_type="AggregateExpression",
                context={"series_type": type(series_expr).__name__},
            )

        if expr.operation == "count":
            return series_expr.count()
        elif expr.operation == "sum":
            return series_expr.sum(expr.field)
        elif expr.operation == "avg":
            return series_expr.avg(expr.field)
        elif expr.operation == "max":
            return series_expr.max(expr.field)
        elif expr.operation == "min":
            return series_expr.min(expr.field)
        else:
            raise EvaluationError(
                f"Unknown aggregation operation: {expr.operation}",
                node_type="AggregateExpression",
                context={"operation": expr.operation, "field": expr.field},
            )

    def _eval_time_shift_expression(
        self,
        expr: TimeShiftNode,
        children_outputs: list[Series[Any]],
        context: dict[str, Series[Any]],
    ) -> Series[Any]:
        """Evaluate TimeShiftExpression using Series shift/change methods."""
        if len(children_outputs) >= 1:
            series_expr = children_outputs[0]
        else:
            raise ValueError("TimeShiftNode requires 1 evaluated child")

        from ...exceptions import EvaluationError

        if not isinstance(series_expr, Series):
            raise EvaluationError(
                f"Expected Series for time shift, got {type(series_expr)}",
                node_type="TimeShiftExpression",
                context={"series_type": type(series_expr).__name__},
            )

        # Parse shift string to extract periods
        periods = self._parse_shift_periods(expr.shift)

        # Apply operation if specified
        if expr.operation == "change":
            return series_expr.change(periods)
        elif expr.operation == "change_pct":
            return series_expr.change_pct(periods)
        elif expr.operation is None:
            # Simple shift
            return series_expr.shift(-periods)  # Negative for "ago" (looking back)
        else:
            raise EvaluationError(
                f"Unknown time shift operation: {expr.operation}",
                node_type="TimeShiftExpression",
                context={"operation": expr.operation, "shift": expr.shift},
            )

    def _parse_shift_periods(self, shift: str) -> int:
        """Parse shift string to extract number of periods.

        Supports formats:
        - "24h_ago" -> 24 periods
        - "1h" -> 1 period
        - "1" -> 1 period
        """
        periods = 1  # default

        if shift.endswith("_ago"):
            shift_part = shift[:-4]  # Remove "_ago"
            if shift_part.endswith("h"):
                hours = int(shift_part[:-1])
                periods = hours
            elif shift_part.endswith("m"):
                minutes = int(shift_part[:-1])
                periods = minutes // 60  # Convert to hours (rough approximation)
            else:
                try:
                    periods = int(shift_part)
                except ValueError:
                    from ...exceptions import EvaluationError

                    raise EvaluationError(
                        f"Invalid shift format: {shift}",
                        node_type="TimeShiftExpression",
                        context={"shift": shift},
                    )
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
                from ...exceptions import EvaluationError

                raise EvaluationError(
                    f"Invalid shift format: {shift}",
                    node_type="TimeShiftExpression",
                    context={"shift": shift},
                )

        return periods

    def _eval_indicator_node(
        self,
        node: CallNode,
        children_outputs: list[Series[Any]],
        context: dict[str, Series[Any]],
    ) -> Series[Any]:
        """Evaluate CallNode."""
        from ...registry.registry import get_global_registry

        registry = get_global_registry()

        if node.name not in registry._indicators:
            from ...exceptions import UnsupportedIndicatorError

            raise UnsupportedIndicatorError(
                f"Indicator '{node.name}' not found in registry",
                indicator=node.name,
                reason="Indicator not registered",
            )
        indicator_func = registry._indicators[node.name]

        # Map evaluated children back to args and kwargs
        eval_args = children_outputs[: len(node.args)]
        eval_kwargs = {}

        kwarg_outputs = children_outputs[len(node.args) :]
        for key, val in zip(sorted(node.kwargs.keys()), kwarg_outputs):
            eval_kwargs[key] = val

        if node.input_expr is not None and len(eval_args) > 0:
            input_series_result = eval_args[0]
            remaining_args = eval_args[1:]

            if isinstance(input_series_result, Series):
                return indicator_func(SeriesContext(close=input_series_result), *remaining_args, **eval_kwargs)

            # Multi-output flow (e.g. enter(bbands(...))). Preserve original context
            # and pass nested result as the first positional indicator argument.
            series_context = SeriesContext(
                close=context.get("close"),
                open=context.get("open"),
                high=context.get("high"),
                low=context.get("low"),
                volume=context.get("volume"),
                trades=context.get("trades"),
                orderbook=context.get("orderbook"),
                liquidation=context.get("liquidation"),
            )
            return indicator_func(series_context, input_series_result, *remaining_args, **eval_kwargs)

        return indicator_func(SeriesContext(**context), *eval_args, **eval_kwargs)

    def clear_cache(self) -> None:
        """Clear the evaluation cache."""
        self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys())[:10],  # First 10 keys as sample
        }
