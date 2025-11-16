"""Expression analysis utilities.

Provides helper functions to analyze expressions and report requirements,
capabilities, and potential issues before deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..dsl import (
    StrategyExpression,
    extract_indicator_nodes,
    parse_expression_text,
)
from .validate import validate


@dataclass
class AnalysisResult:
    """Result of expression analysis.

    Attributes:
        expression: The analyzed expression (as string or parsed AST)
        valid: Whether the expression is valid and can be compiled
        errors: List of error messages
        warnings: List of warning messages (including capability warnings)
        indicators: List of indicator names used
        data_requirements: List of DataRequirement objects
        required_sources: List of required source types (e.g., 'ohlcv', 'trades')
        required_exchanges: List of required exchange names
        required_timeframes: List of required timeframes
        min_lookback: Minimum number of bars needed for evaluation
        capability_warnings: List of capability-specific warnings
        plan: Optional PlanResult if planning was successful
    """

    expression: str | StrategyExpression
    valid: bool
    errors: list[str]
    warnings: list[str]
    indicators: list[str]
    data_requirements: list[Any]  # DataRequirement objects
    required_sources: list[str]
    required_exchanges: list[str]
    required_timeframes: list[str]
    min_lookback: int
    capability_warnings: list[str]
    plan: Any | None = None  # PlanResult if available

    def to_dict(self) -> dict[str, Any]:
        """Convert analysis result to dictionary for serialization."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "indicators": self.indicators,
            "data_requirements": [
                {
                    "source": req.source,
                    "field": req.field,
                    "symbol": req.symbol,
                    "exchange": req.exchange,
                    "timeframe": req.timeframe,
                    "min_lookback": req.min_lookback,
                    "aggregation_params": req.aggregation_params,
                }
                for req in self.data_requirements
            ],
            "required_sources": self.required_sources,
            "required_exchanges": self.required_exchanges,
            "required_timeframes": self.required_timeframes,
            "min_lookback": self.min_lookback,
            "capability_warnings": self.capability_warnings,
            "plan": self.plan.to_dict() if self.plan else None,
        }


def analyze(
    expression: str | StrategyExpression,
    *,
    exchange: str | None = None,
    check_capabilities: bool = True,
) -> AnalysisResult:
    """
    Analyze an expression and report requirements, capabilities, and warnings.

    This is a comprehensive helper that combines validation, planning, and
    capability checking to provide a complete analysis of an expression before
    deployment.

    Args:
        expression: Expression text (e.g., "(sma(20) > sma(50))") or parsed StrategyExpression
        exchange: Optional exchange name for capability checking
        check_capabilities: Whether to check exchange capabilities (default: True)

    Returns:
        AnalysisResult with comprehensive information about the expression

    Example:
        >>> result = analyze("sma(20) > sma(50)", exchange="binance")
        >>> print(f"Valid: {result.valid}")
        >>> print(f"Required sources: {result.required_sources}")
        >>> print(f"Warnings: {result.warnings}")
    """
    # Step 1: Validate the expression
    validation_result = validate(expression, exchange=exchange, check_capabilities=check_capabilities)

    # Step 2: Extract indicators
    try:
        if isinstance(expression, str):
            strategy_expr = parse_expression_text(expression)
        else:
            strategy_expr = expression

        indicator_nodes = extract_indicator_nodes(strategy_expr)
        indicator_names = [node.name for node in indicator_nodes]
    except Exception:
        indicator_names = validation_result.indicators

    # Step 3: Plan the expression to get requirements
    data_requirements: list[Any] = []
    required_sources: list[str] = []
    required_exchanges: list[str] = []
    required_timeframes: list[str] = []
    min_lookback = 0
    plan = None

    if validation_result.valid and validation_result.plan:
        plan = validation_result.plan
        requirements = plan.requirements

        # Extract data requirements
        data_requirements = list(requirements.data_requirements)
        required_sources = list(requirements.required_sources)
        required_exchanges = list(requirements.required_exchanges)

        # Extract timeframes from field requirements
        timeframes = set()
        for field_req in requirements.fields:
            if field_req.timeframe:
                timeframes.add(field_req.timeframe)
        for data_req in requirements.data_requirements:
            if data_req.timeframe:
                timeframes.add(data_req.timeframe)
        required_timeframes = sorted(list(timeframes))

        # Compute minimum lookback
        if requirements.fields:
            min_lookback = max((field.min_lookback for field in requirements.fields), default=0)
        if requirements.data_requirements:
            data_lookback = max((req.min_lookback for req in requirements.data_requirements), default=0)
            min_lookback = max(min_lookback, data_lookback)
    else:
        # Try to compute lookback from indicators even if planning failed
        try:
            if isinstance(expression, str):
                strategy_expr = parse_expression_text(expression)
            else:
                strategy_expr = expression

            from ..dsl import compute_trim

            indicator_nodes = extract_indicator_nodes(strategy_expr)
            min_lookback = compute_trim(indicator_nodes)
        except Exception:
            min_lookback = 0

    # Step 4: Extract capability warnings
    capability_warnings = []
    if check_capabilities:
        # Capability warnings are already in validation_result.warnings
        # but we can extract them specifically if needed
        for warning in validation_result.warnings:
            if any(
                keyword in warning.lower() for keyword in ["capability", "not supported", "not available", "exchange"]
            ):
                capability_warnings.append(warning)

    return AnalysisResult(
        expression=expression,
        valid=validation_result.valid,
        errors=validation_result.errors,
        warnings=validation_result.warnings,
        indicators=indicator_names,
        data_requirements=data_requirements,
        required_sources=required_sources,
        required_exchanges=required_exchanges,
        required_timeframes=required_timeframes,
        min_lookback=min_lookback,
        capability_warnings=capability_warnings,
        plan=plan,
    )
