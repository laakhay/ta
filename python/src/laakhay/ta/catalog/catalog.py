"""Indicator catalog utilities backed by Rust metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..registry.models import IndicatorHandle
from ..registry.registry import get_global_registry
from .rust_catalog import list_rust_catalog, rust_catalog_available


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
    handle: IndicatorHandle | None
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
    """Builds indicator catalog from Rust metadata."""

    def __init__(self) -> None:
        self._registry = get_global_registry()

    def build_catalog(self) -> dict[str, IndicatorDescriptor]:
        """Build complete indicator catalog from Rust metadata."""
        if not rust_catalog_available():
            raise RuntimeError("Rust catalog is unavailable; ta_py metadata endpoints are required")
        rust_catalog = list_rust_catalog()
        catalog: dict[str, IndicatorDescriptor] = {}
        for name, meta in rust_catalog.items():
            handle = self._registry.get(name)
            catalog[name.lower()] = self._descriptor_from_rust_meta(name, meta, handle)
        return catalog

    def describe_indicator(self, name: str, handle: IndicatorHandle | None = None) -> IndicatorDescriptor:
        """Describe a single indicator from Rust metadata."""
        if not rust_catalog_available():
            raise RuntimeError("Rust catalog is unavailable; ta_py metadata endpoints are required")
        indicator_id = name.lower()
        rust_catalog = list_rust_catalog()
        meta = rust_catalog.get(indicator_id)
        if meta is None:
            raise ValueError(f"Indicator '{name}' not found in Rust catalog")
        resolved_handle = handle or self._registry.get(indicator_id)
        return self._descriptor_from_rust_meta(indicator_id, meta, resolved_handle)

    @staticmethod
    def _build_parameter_definitions(params_meta: tuple[dict[str, Any], ...]) -> list[ParameterDefinition]:
        params: list[ParameterDefinition] = []
        for param in params_meta:
            param_name = str(param.get("name", ""))
            params.append(
                ParameterDefinition(
                    name=param_name,
                    param_type=str(param.get("kind", "unknown")),
                    required=bool(param.get("required", False)),
                    description=str(param.get("description", "")),
                    default_value=param.get("default"),
                    public_default=param.get("default"),
                    supported=True,
                )
            )
        return params

    @staticmethod
    def _build_outputs(outputs_meta: tuple[dict[str, Any], ...]) -> tuple[list[OutputDefinition], tuple[str, ...]]:
        outputs: list[OutputDefinition] = []
        aliases: list[str] = []
        output_names = {str(output.get("name", "result")) for output in outputs_meta}
        for output in outputs_meta:
            output_name = str(output.get("name", "result"))
            kind = str(output.get("kind", "line"))
            aliases.append(output_name)
            metadata: dict[str, Any] = {"role": kind}
            if output_name == "upper" and "lower" in output_names:
                metadata["area_pair"] = "lower"
            if output_name == "lower" and "upper" in output_names:
                metadata["area_pair"] = "upper"
            outputs.append(
                OutputDefinition(
                    name=output_name,
                    kind=kind,
                    description=str(output.get("description", "")),
                    metadata=metadata,
                )
            )
        return outputs, tuple(aliases)

    def _descriptor_from_rust_meta(
        self,
        indicator_id: str,
        meta: Mapping[str, Any],
        handle: IndicatorHandle | None,
    ) -> IndicatorDescriptor:
        parameters = self._build_parameter_definitions(meta.get("params", ()))
        outputs, aliases = self._build_outputs(meta.get("outputs", ()))
        return IndicatorDescriptor(
            name=indicator_id,
            description=str(meta.get("display_name") or indicator_id),
            category=str(meta.get("category", "custom")),
            handle=handle,
            parameters=parameters,
            outputs=outputs,
            supported=True,
            tuple_aliases=aliases,
        )


def list_catalog() -> dict[str, IndicatorDescriptor]:
    """Build and return complete indicator catalog.

    Returns:
        Dictionary mapping indicator names (lowercase) to descriptors
    """
    builder = CatalogBuilder()
    return builder.build_catalog()


def list_catalog_metadata() -> dict[str, dict[str, Any]]:
    """Return canonical indicator metadata from Rust."""
    if not rust_catalog_available():
        raise RuntimeError("Rust catalog is unavailable; ta_py metadata endpoints are required")
    return list_rust_catalog()


def describe_indicator(name: str) -> IndicatorDescriptor:
    """Describe a single indicator by name.

    Args:
        name: Indicator name

    Returns:
        IndicatorDescriptor for the indicator

    Raises:
        ValueError: If indicator not found
    """
    builder = CatalogBuilder()
    return builder.describe_indicator(name)
