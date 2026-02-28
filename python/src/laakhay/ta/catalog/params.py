"""Parameter parsing and coercion utilities."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any


class ParameterCoercionError(ValueError):
    """Error raised during parameter coercion."""

    def __init__(self, message: str, parameter_name: str | None = None):
        super().__init__(message)
        self.parameter_name = parameter_name


class ParameterParser:
    """Parses and coerces indicator parameters.

    This class handles parameter validation and coercion without HTTP dependencies,
    making it suitable for use in library code, CLIs, and other non-HTTP contexts.
    """

    def __init__(self) -> None:
        """Initialize parameter parser."""
        pass

    def coerce_parameters(
        self, parameter_specs: dict[str, dict[str, Any]], raw_params: Mapping[str, Any]
    ) -> dict[str, Any]:
        """
        Coerce and validate parameters against specifications.

        Args:
            parameter_specs: Dictionary mapping parameter names to their specifications
                           (from TypeParser.classify_parameter)
            raw_params: Raw parameter values from request/user input

        Returns:
            Coerced and validated parameters

        Raises:
            ParameterCoercionError: If parameters are invalid
        """
        parsed: dict[str, Any] = {}
        for param_name, spec in parameter_specs.items():
            raw_value = raw_params.get(param_name)
            value = self.coerce_value(spec, raw_value)
            if value is not None:
                parsed[param_name] = value

        # Check for unknown parameters
        unknown = set(raw_params.keys()) - set(parameter_specs.keys())
        if unknown:
            raise ParameterCoercionError(f"Unexpected parameters: {', '.join(sorted(unknown))}")

        return parsed

    def coerce_value(self, spec: dict[str, Any], raw_value: Any) -> Any:
        """
        Coerce a raw value to the expected parameter type.

        Args:
            spec: Parameter specification (from TypeParser.classify_parameter)
            raw_value: Raw value to coerce

        Returns:
            Coerced value

        Raises:
            ParameterCoercionError: If value is required but missing or cannot be coerced
        """
        param_name = spec.get("name", "unknown")
        required = spec.get("required", False)
        default_value = spec.get("default_value")
        param_type = spec.get("param_type", "json")
        collection = spec.get("collection", False)
        collection_python_type = spec.get("collection_python_type")
        item_type = spec.get("item_type")
        options = spec.get("options")

        if raw_value is None or raw_value == "":
            if required and default_value is None:
                raise ParameterCoercionError(f"Parameter '{param_name}' is required", parameter_name=param_name)
            return default_value

        if isinstance(raw_value, list) and not collection:
            raw_value = raw_value[-1]

        try:
            if param_type == "int":
                return int(raw_value)
            if param_type == "float":
                return float(raw_value)
            if param_type == "bool":
                if isinstance(raw_value, bool):
                    return raw_value
                if isinstance(raw_value, str):
                    normalized = raw_value.strip().lower()
                    if normalized in {"1", "true", "yes"}:
                        return True
                    if normalized in {"0", "false", "no"}:
                        return False
                return bool(raw_value)
            if param_type == "string":
                return str(raw_value)
            if param_type == "enum":
                value = raw_value
                if isinstance(value, str):
                    value = value.strip()
                if options and value not in options:
                    raise ParameterCoercionError(
                        f"Parameter '{param_name}' must be one of {options}",
                        parameter_name=param_name,
                    )
                return value
            if param_type == "json":
                parsed = self._parse_json(raw_value)
                if collection:
                    if isinstance(parsed, Iterable) and not isinstance(parsed, str | bytes | dict):
                        items = []
                        for item in parsed:
                            if item_type == "int":
                                items.append(int(item))
                            elif item_type == "float":
                                items.append(float(item))
                            elif item_type == "bool":
                                items.append(bool(item))
                            elif item_type == "string":
                                items.append(str(item))
                            else:
                                items.append(item)
                        if collection_python_type is tuple:
                            return tuple(items)
                        return items
                    raise ParameterCoercionError(
                        f"Parameter '{param_name}' expects an array value",
                        parameter_name=param_name,
                    )
                return parsed
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ParameterCoercionError(
                f"Invalid value for parameter '{param_name}'",
                parameter_name=param_name,
            ) from exc

        return raw_value

    @staticmethod
    def _parse_json(value: Any) -> Any:
        """Parse JSON string or return value as-is."""
        if isinstance(value, str):
            return json.loads(value)
        return value


def coerce_parameter(param_type: str, value: Any, default: Any = None, options: list[Any] | None = None) -> Any:
    """Convenience function to coerce a single parameter value.

    Args:
        param_type: Parameter type (int, float, string, bool, enum, json)
        value: Value to coerce
        default: Default value if value is None
        options: Valid options for enum types

    Returns:
        Coerced value

    Raises:
        ParameterCoercionError: If coercion fails
    """
    parser = ParameterParser()
    spec = {
        "name": "param",
        "param_type": param_type,
        "required": default is None,
        "default_value": default,
        "options": options,
        "collection": False,
    }
    return parser.coerce_value(spec, value)


def coerce_parameters(parameter_specs: dict[str, dict[str, Any]], raw_params: Mapping[str, Any]) -> dict[str, Any]:
    """Convenience function to coerce multiple parameters.

    Args:
        parameter_specs: Dictionary mapping parameter names to their specifications
        raw_params: Raw parameter values

    Returns:
        Coerced and validated parameters

    Raises:
        ParameterCoercionError: If coercion fails
    """
    parser = ParameterParser()
    return parser.coerce_parameters(parameter_specs, raw_params)
