"""Expression preview and evaluation utilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ...core import Series
from ...core.dataset import Dataset
from ...data.dataset import dataset_from_bars, trim_dataset
from ..dsl import (
    StrategyExpression,
    compile_expression,
    compute_trim,
    extract_indicator_nodes,
    parse_expression_text,
)


@dataclass
class PreviewResult:
    """Result of expression preview evaluation.

    Attributes:
        series: The resulting Series from evaluating the expression.
               If evaluating against Dataset, this is the first series.
        triggers: List of trigger points where boolean expressions are True.
                 Each trigger is a dict with 'timestamp', 'value', and 'index' keys.
        indicators: List of indicator nodes used in the expression.
        trim: Number of bars to trim due to indicator lookback requirements.
        requirements: Optional SignalRequirements from expression planning.
        plan: Optional PlanResult if planning was performed.
    """

    series: Series[Any]
    triggers: list[dict[str, Any]]
    indicators: list[Any]
    trim: int
    requirements: Any | None = None  # SignalRequirements from planner
    plan: Any | None = None  # PlanResult if available


def preview(
    expression: str | StrategyExpression,
    *,
    bars: Sequence[Mapping[str, Any]] | None = None,
    dataset: Dataset | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> PreviewResult:
    """Preview and evaluate a strategy expression.

    This function provides an end-to-end expression runner that:
    1. Parses the expression (if string)
    2. Compiles it to an executable Expression
    3. Computes required lookback trim
    4. Builds/trims dataset if bars are provided
    5. Evaluates the expression
    6. Extracts trigger points (where boolean results are True)

    Args:
        expression: Expression text (e.g., "(sma(20) > sma(50))") or parsed StrategyExpression
        bars: Optional raw OHLCV bar data. Must provide either bars or dataset.
        dataset: Optional pre-built Dataset. Must provide either bars or dataset.
        symbol: Symbol name (required if bars provided)
        timeframe: Timeframe (required if bars provided)

    Returns:
        PreviewResult with series, triggers, indicators, and trim information.

    Raises:
        ValueError: If neither bars nor dataset provided, or if bars provided without symbol/timeframe.
        StrategyError: If expression parsing or compilation fails.
    """
    # Parse expression if string
    if isinstance(expression, str):
        strategy_expr = parse_expression_text(expression)
    else:
        strategy_expr = expression

    # Extract indicators and compute trim
    indicator_nodes = extract_indicator_nodes(strategy_expr)
    trim = compute_trim(indicator_nodes)

    # Normalize dataset input
    if dataset is None:
        if bars is None:
            raise ValueError("Must provide either 'bars' or 'dataset'")
        if symbol is None or timeframe is None:
            raise ValueError("Must provide 'symbol' and 'timeframe' when using 'bars'")

        dataset = dataset_from_bars(bars, symbol=symbol, timeframe=timeframe)

    # Trim dataset if needed
    if trim > 0 and symbol and timeframe:
        dataset = trim_dataset(dataset, symbol=symbol, timeframe=timeframe, trim=trim)

    # Compile expression
    compiled_expr = compile_expression(strategy_expr)

    # Evaluate expression
    result = compiled_expr.run(dataset)

    # Extract series and triggers
    if isinstance(result, dict):
        # Multiple series (one per (symbol, timeframe) pair)
        # Use the first one for the main series
        series_keys = sorted(result.keys())
        if not series_keys:
            raise ValueError("Expression evaluation returned no series")
        main_key = series_keys[0]
        series = result[main_key]
    elif isinstance(result, Series):
        series = result
    else:
        raise ValueError(f"Unexpected result type from expression evaluation: {type(result)}")

    # Extract triggers (boolean True values)
    triggers = _extract_triggers(series)

    # Get requirements if available
    try:
        from ..planner import plan_expression

        plan = plan_expression(compiled_expr._node)
        requirements = plan.requirements
    except Exception:
        plan = None
        requirements = None

    return PreviewResult(
        series=series,
        triggers=triggers,
        indicators=indicator_nodes,
        trim=trim,
        requirements=requirements,
        plan=plan,
    )


def _extract_triggers(series: Series[Any]) -> list[dict[str, Any]]:
    """Extract trigger points from a boolean Series.

    A trigger is where the series value is True (for boolean expressions).
    """
    triggers: list[dict[str, Any]] = []

    # Check if this is a boolean series
    if len(series.values) == 0:
        return triggers

    first_value = series.values[0]
    is_boolean = isinstance(first_value, bool) or isinstance(first_value, int | float) and first_value in (0, 1)

    if not is_boolean:
        # Not a boolean series, no triggers
        return triggers

    # Extract True values as triggers
    for i, (timestamp, value) in enumerate(series):
        # Convert to boolean: True, 1, or any truthy value in boolean context
        is_trigger = bool(value) if isinstance(value, int | float | bool) else False
        if is_trigger:
            triggers.append(
                {
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
                    "value": bool(value),
                    "index": i,
                }
            )

    return triggers
