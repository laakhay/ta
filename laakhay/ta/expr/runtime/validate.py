"""Expression validation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...registry.registry import get_global_registry
from ..dsl import (
    StrategyError,
    StrategyExpression,
    compile_expression,
    extract_indicator_nodes,
    parse_expression_text,
)
from .capability_validator import CapabilityValidator


class ExprValidationError(ValueError):
    """Error raised during expression validation.

    Contains structured information about validation failures.
    """

    def __init__(self, message: str, errors: list[str] | None = None, warnings: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []
        self.warnings = warnings or []


@dataclass
class ValidationResult:
    """Result of expression validation.

    Attributes:
        valid: Whether the expression is valid and can be compiled.
        errors: List of error messages (indicator not found, invalid fields, etc.)
        warnings: List of warning messages (deprecated indicators, capability issues, etc.)
        indicators: List of indicator names used in the expression.
        select_fields: List of select fields used (e.g., 'close', 'high', 'hlc3').
        requirements: Optional SignalRequirements if expression was planned.
        plan: Optional PlanResult if expression was planned.
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    indicators: list[str] = field(default_factory=list)
    select_fields: list[str] = field(default_factory=list)
    requirements: Any | None = None  # SignalRequirements from planner
    plan: Any | None = None  # PlanResult if available


# Valid select fields that can be used with the 'select' indicator
VALID_SELECT_FIELDS = {
    # Standard OHLCV fields
    "open",
    "high",
    "low",
    "close",
    "volume",
    # Derived fields
    "hlc3",  # Typical price: (high + low + close) / 3
    "ohlc4",  # Average price: (open + high + low + close) / 4
    "hl2",  # Mid price: (high + low) / 2
    "range",  # High - Low
    "upper_wick",  # High - max(Open, Close)
    "lower_wick",  # min(Open, Close) - Low
    "typical_price",  # Alias for hlc3
    "weighted_close",  # Alias for ohlc4
    "median_price",  # Alias for hl2
    # Common aliases
    "price",  # Alias for close
    "o",  # Short alias for open
    "h",  # Short alias for high
    "l",  # Short alias for low
    "c",  # Short alias for close
    "v",  # Short alias for volume
}


def validate(
    expression: str | StrategyExpression,
    exchange: str | None = None,
    check_capabilities: bool = True,
) -> ValidationResult:
    """Validate a strategy expression.

    Performs comprehensive validation:
    - Parses the expression (syntax check)
    - Verifies all indicators exist in the registry
    - Validates select field names against whitelist
    - Validates indicator parameters against their schemas
    - Attempts a dry-run compile

    Args:
        expression: Expression text (e.g., "(sma(20) > sma(50))") or parsed StrategyExpression

    Returns:
        ValidationResult with validation status, errors, warnings, and metadata.
    """
    errors: list[str] = []
    warnings: list[str] = []
    indicator_names: list[str] = []
    select_fields_used: list[str] = []

    # Step 1: Parse expression
    try:
        if isinstance(expression, str):
            strategy_expr = parse_expression_text(expression)
        else:
            strategy_expr = expression
    except StrategyError as e:
        errors.append(f"Failed to parse expression: {str(e)}")
        return ValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            indicators=indicator_names,
            select_fields=select_fields_used,
        )
    except Exception as e:
        errors.append(f"Unexpected error during parsing: {str(e)}")
        return ValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            indicators=indicator_names,
            select_fields=select_fields_used,
        )

    # Step 2: Extract indicators and validate them
    try:
        indicator_nodes = extract_indicator_nodes(strategy_expr)
        registry = get_global_registry()

        for node in indicator_nodes:
            indicator_name = node.name
            indicator_names.append(indicator_name)

            # Check if indicator exists in registry
            registry_handle = registry.get(indicator_name)
            if registry_handle is None:
                # Suggest similar indicators
                available = registry.list_all_names()
                similar = [
                    n for n in available if indicator_name.lower() in n.lower() or n.lower() in indicator_name.lower()
                ][:3]
                suggestion = f" Did you mean: {', '.join(similar)}?" if similar else ""
                errors.append(f"Indicator '{indicator_name}' not found in registry.{suggestion}")
                continue

            # Validate select field if this is a 'select' indicator
            if indicator_name == "select":
                field_param = node.params.get("field")
                if field_param:
                    field_str = str(field_param).lower()
                    select_fields_used.append(field_str)
                    if field_str not in VALID_SELECT_FIELDS:
                        errors.append(
                            f"Invalid select field '{field_param}'. "
                            f"Valid fields: {', '.join(sorted(VALID_SELECT_FIELDS))}"
                        )

            # Validate parameters against schema
            try:
                schema = registry_handle.schema
                param_schemas = schema.parameters

                # Check for unknown parameters
                for param_name in node.params:
                    if param_name not in param_schemas:
                        warnings.append(
                            f"Indicator '{indicator_name}' has unknown parameter '{param_name}'. "
                            f"Expected parameters: {', '.join(param_schemas.keys())}"
                        )

                # Validate required parameters (skip 'ctx' which is internal)
                for param_name, param_schema in param_schemas.items():
                    if param_name.lower() in ("ctx", "context"):
                        continue  # Skip internal context parameter
                    if param_schema.required and param_name not in node.params:
                        errors.append(
                            f"Indicator '{indicator_name}' requires parameter '{param_name}' but it was not provided"
                        )

            except Exception as e:
                warnings.append(f"Could not validate parameters for '{indicator_name}': {str(e)}")

    except Exception as e:
        errors.append(f"Error extracting indicators: {str(e)}")

    # Step 3: Attempt dry-run compile
    try:
        compiled_expr = compile_expression(strategy_expr)
    except StrategyError as e:
        errors.append(f"Compilation failed: {str(e)}")
    except Exception as e:
        errors.append(f"Unexpected error during compilation: {str(e)}")
        compiled_expr = None

    # Step 4: Check capabilities if requested and get plan
    plan = None
    requirements = None
    if check_capabilities and compiled_expr is not None:
        try:
            from ..planner import plan_expression

            plan = plan_expression(compiled_expr._node)
            requirements = plan.requirements
            validator = CapabilityValidator()
            capability_warnings = validator.validate_plan(plan, exchange=exchange)
            warnings.extend(capability_warnings)
        except Exception as e:
            # Don't fail validation if capability check fails
            warnings.append(f"Could not validate capabilities: {str(e)}")

    # Determine if expression is valid
    valid = len(errors) == 0

    return ValidationResult(
        valid=valid,
        errors=errors,
        warnings=warnings,
        indicators=list(set(indicator_names)),  # Remove duplicates
        select_fields=list(set(select_fields_used)),  # Remove duplicates
        requirements=requirements,
        plan=plan,
    )
