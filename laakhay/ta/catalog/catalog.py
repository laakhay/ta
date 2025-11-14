"""Indicator catalog building utilities."""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, get_type_hints

from ..api.namespace import ensure_namespace_registered
from ..registry import list_indicators
from ..registry.models import IndicatorHandle
from ..registry.registry import get_global_registry
from .type_parser import TypeParser

# Tuple alias overrides for multi-output indicators
_TUPLE_ALIAS_OVERRIDES: dict[str, tuple[str, ...]] = {
    "macd": ("macd", "signal", "histogram"),
    "bbands": ("upper", "middle", "lower"),
    "stochastic": ("k", "d"),
}

# Category hints based on module paths
_CATEGORY_HINTS = {
    "trend": "trend",
    "momentum": "momentum",
    "volatility": "volatility",
    "volume": "volume",
    "pattern": "pattern",
    "primitives": "primitive",
}


@dataclass
class ParameterDefinition:
    """Definition of an indicator parameter."""

    name: str
    param_type: str  # int, float, string, bool, enum, json
    required: bool
    description: str = ""
    python_type: Any | None = None
    default_value: Any | None = None
    public_default: Any | None = None
    options: list[Any] | None = None
    collection: bool = False
    collection_python_type: type | None = None
    item_type: str | None = None
    item_python_type: Any | None = None
    supported: bool = True


@dataclass
class OutputDefinition:
    """Definition of an indicator output."""

    name: str
    kind: str = "series"  # series, scalar, metadata
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IndicatorDescriptor:
    """Complete descriptor for an indicator."""

    name: str
    description: str
    category: str
    handle: IndicatorHandle
    parameters: list[ParameterDefinition]
    outputs: list[OutputDefinition]
    supported: bool
    tuple_aliases: tuple[str, ...] = ()
    param_map: dict[str, ParameterDefinition] = field(init=False, repr=False, default_factory=dict)

    def __post_init__(self) -> None:
        """Build parameter map for quick lookup."""
        self.param_map = {param.name: param for param in self.parameters}

    def get_parameter_specs(self) -> dict[str, dict[str, Any]]:
        """Get parameter specifications as dictionaries for coercion."""
        return {
            param.name: {
                "name": param.name,
                "param_type": param.param_type,
                "required": param.required,
                "default_value": param.default_value,
                "public_default": param.public_default,
                "options": param.options,
                "collection": param.collection,
                "collection_python_type": param.collection_python_type,
                "item_type": param.item_type,
                "item_python_type": param.item_python_type,
                "supported": param.supported,
            }
            for param in self.parameters
        }


class CatalogBuilder:
    """Builds indicator catalog from registry."""

    def __init__(self) -> None:
        """Initialize catalog builder."""
        self._registry = get_global_registry()
        self._type_parser = TypeParser()

    def build_catalog(self) -> dict[str, IndicatorDescriptor]:
        """Build complete indicator catalog.

        Returns:
            Dictionary mapping indicator names (lowercase) to descriptors
        """
        # Ensure namespace helpers are registered
        try:
            ensure_namespace_registered()
        except Exception:
            pass  # Continue even if registration fails

        catalog: dict[str, IndicatorDescriptor] = {}
        for name in sorted(list_indicators()):
            handle = self._registry.get(name)
            if handle is None:
                continue
            func_module = getattr(handle.func, "__module__", "")
            # Include 'select' primitive even though it's not in indicators module
            if "laakhay.ta.indicators" not in func_module and name != "select":
                continue  # filter primitives/helpers (except select)
            descriptor = self.describe_indicator(name, handle)
            catalog[name.lower()] = descriptor
        return catalog

    def describe_indicator(self, name: str, handle: IndicatorHandle) -> IndicatorDescriptor:
        """Describe a single indicator.

        Args:
            name: Indicator name
            handle: Indicator handle from registry

        Returns:
            IndicatorDescriptor with all metadata
        """
        schema = handle.schema
        func = handle.func
        hints = get_type_hints(func)
        signature = inspect.signature(func)
        parameters = self._build_parameter_definitions(signature, hints)
        outputs, aliases = self._build_outputs(name, schema.output_metadata)
        supported = all(param.supported for param in parameters)
        category = self._infer_category(func.__module__)
        description = schema.description or func.__doc__ or name
        return IndicatorDescriptor(
            name=name,
            description=description.strip() if description else name,
            category=category,
            handle=handle,
            parameters=parameters,
            outputs=outputs,
            supported=supported,
            tuple_aliases=aliases,
        )

    def _build_parameter_definitions(
        self,
        signature: inspect.Signature,
        hints: Mapping[str, Any],
    ) -> list[ParameterDefinition]:
        """Build parameter definitions from function signature."""
        params: list[ParameterDefinition] = []
        for param in signature.parameters.values():
            if param.name == "ctx":
                continue  # Skip internal context parameter
            annotation = hints.get(param.name, param.annotation)
            classification = self._type_parser.classify_parameter(param.name, annotation, param.default)
            # Get parameter description from schema if available
            schema_param = signature.parameters.get(param.name)
            description = getattr(schema_param, "description", None) if schema_param else None
            if not description:
                description = f"Parameter {param.name}"
            params.append(
                ParameterDefinition(
                    name=classification["name"],
                    param_type=classification["param_type"],
                    required=classification["required"],
                    description=description,
                    python_type=classification["python_type"],
                    default_value=classification["default_value"],
                    public_default=classification["public_default"],
                    options=classification.get("options"),
                    collection=classification["collection"],
                    collection_python_type=classification.get("collection_python_type"),
                    item_type=classification.get("item_type"),
                    item_python_type=classification.get("item_python_type"),
                    supported=classification["supported"],
                )
            )
        return params

    def _build_outputs(
        self,
        indicator_name: str,
        metadata: dict[str, dict[str, Any]],
    ) -> tuple[list[OutputDefinition], tuple[str, ...]]:
        """Build output definitions."""
        outputs: list[OutputDefinition] = []
        alias_override = _TUPLE_ALIAS_OVERRIDES.get(indicator_name, ())
        if metadata:
            for name, meta in metadata.items():
                outputs.append(
                    OutputDefinition(
                        name=name,
                        kind=meta.get("role", "series"),
                        description=meta.get("description"),
                        metadata=meta,
                    )
                )
        elif alias_override:
            for alias in alias_override:
                outputs.append(OutputDefinition(name=alias))
        else:
            outputs.append(OutputDefinition(name="result"))
        return outputs, alias_override

    @staticmethod
    def _infer_category(module_name: str | None) -> str:
        """Infer indicator category from module name."""
        if not module_name:
            return "custom"
        for keyword, category in _CATEGORY_HINTS.items():
            if f".{keyword}." in module_name:
                return category
        return "custom"


def list_catalog() -> dict[str, IndicatorDescriptor]:
    """Build and return complete indicator catalog.

    Returns:
        Dictionary mapping indicator names (lowercase) to descriptors
    """
    builder = CatalogBuilder()
    return builder.build_catalog()


def describe_indicator(name: str) -> IndicatorDescriptor:
    """Describe a single indicator by name.

    Args:
        name: Indicator name

    Returns:
        IndicatorDescriptor for the indicator

    Raises:
        ValueError: If indicator not found
    """
    registry = get_global_registry()
    handle = registry.get(name)
    if handle is None:
        raise ValueError(f"Indicator '{name}' not found in registry")
    builder = CatalogBuilder()
    return builder.describe_indicator(name, handle)
