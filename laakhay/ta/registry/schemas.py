"""Schema dataclasses for indicator metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.series import Series

# -----------------------------------------------------------------------------
# Strict IndicatorSpec models (Phase 1.1)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class InputSlotSpec:
    """Optional input expression slot (source/field binding)."""

    name: str
    description: str = ""
    required: bool = True
    default_source: str | None = None  # e.g., "ohlcv"
    default_field: str | None = None  # e.g., "close"


@dataclass(frozen=True)
class ParamSpec:
    """Strict parameter specification (extends ParamSchema with min/max)."""

    name: str
    type: type
    default: Any | None = None
    required: bool = True
    description: str = ""
    valid_values: list[Any] | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None


@dataclass(frozen=True)
class OutputSpec:
    """Strict output specification (extends OutputSchema with role/polarity)."""

    name: str
    type: type
    description: str = ""
    role: str = "line"
    polarity: str | None = None  # e.g., "high", "low" for swing levels


@dataclass(frozen=True)
class SemanticsSpec:
    """Lookback and data requirements."""

    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()
    lookback_params: tuple[str, ...] = ()
    default_lookback: int | None = None
    input_field: str | None = None
    input_series_param: str | None = None


@dataclass(frozen=True)
class RuntimeBindingSpec:
    """Kernel binding for runtime dispatch."""

    kernel_id: str


@dataclass(frozen=True)
class ConstraintSpec:
    """Cross-parameter constraint."""

    param_names: tuple[str, ...]
    constraint_type: str  # e.g., "less_than", "greater_than", "sum_bounds"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IndicatorSpec:
    """Top-level strict indicator specification."""

    name: str
    description: str = ""
    inputs: tuple[InputSlotSpec, ...] = ()
    params: dict[str, ParamSpec] = field(default_factory=dict)
    outputs: dict[str, OutputSpec] = field(default_factory=dict)
    semantics: SemanticsSpec = field(default_factory=SemanticsSpec)
    runtime_binding: RuntimeBindingSpec = field(default_factory=lambda: RuntimeBindingSpec(kernel_id=""))
    constraints: tuple[ConstraintSpec, ...] = ()
    aliases: tuple[str, ...] = ()
    param_aliases: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate indicator spec."""
        if not self.name:
            raise ValueError("Indicator name must be a non-empty string")


# -----------------------------------------------------------------------------
# Legacy schema models (kept for backward compatibility)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ParamSchema:
    """Schema definition for an indicator parameter."""

    name: str
    type: type
    default: Any | None = None
    required: bool = True
    description: str = ""
    valid_values: list[Any] | None = None

    def __post_init__(self) -> None:
        """Validate parameter schema."""
        if not self.name:
            raise ValueError("Parameter name must be a non-empty string")

        # Required parameters must not provide a default.
        if self.required and self.default is not None:
            raise ValueError("Required parameters cannot have default values")

        # Optional parameters may have None default; ensure selectable defaults are legitimate.
        if not self.required and self.default is not None and self.valid_values is not None:
            if self.default not in self.valid_values:
                raise ValueError(f"Default value {self.default} not in valid_values")


@dataclass(frozen=True)
class OutputSchema:
    """Schema definition for an indicator output."""

    name: str
    type: type
    description: str = ""

    def __post_init__(self) -> None:
        """Validate output schema."""
        if not self.name:
            raise ValueError("Output name must be a non-empty string")


@dataclass(frozen=True)
class IndicatorSchema:
    """Complete schema for an indicator."""

    name: str
    description: str = ""
    parameters: dict[str, ParamSchema] = field(default_factory=lambda: dict[str, ParamSchema]())
    outputs: dict[str, OutputSchema] = field(default_factory=lambda: dict[str, OutputSchema]())
    aliases: list[str] = field(default_factory=lambda: list[str]())
    metadata: IndicatorMetadata = field(default_factory=lambda: IndicatorMetadata())
    output_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    parameter_aliases: dict[str, str] = field(default_factory=dict)  # alias -> canonical_name

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                name: {
                    "type": param.type.__name__,
                    "default": param.default,
                    "required": param.required,
                    "description": param.description,
                    "valid_values": param.valid_values,
                }
                for name, param in self.parameters.items()
            },
            "outputs": {
                name: {
                    "type": output.type.__name__,
                    "description": output.description,
                }
                for name, output in self.outputs.items()
            },
            "aliases": self.aliases,
            "metadata": self.metadata.to_dict(),
            "output_metadata": self.output_metadata,
            "parameter_aliases": self.parameter_aliases,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndicatorSchema:
        """Create schema from dictionary representation."""
        # Convert type names back to types (simplified for basic types)
        type_mapping = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "Series": Series,
        }

        parameters: dict[str, ParamSchema] = {}
        for name, param_data in data.get("parameters", {}).items():
            param_type_name: str = param_data["type"]
            if param_type_name not in type_mapping:
                raise ValueError(f"Unsupported parameter type: {param_type_name}")
            param_type: type = type_mapping[param_type_name]
            parameters[name] = ParamSchema(
                name=name,
                type=param_type,
                default=param_data.get("default"),
                required=param_data.get("required", True),
                description=param_data.get("description", ""),
                valid_values=param_data.get("valid_values"),
            )

        outputs: dict[str, OutputSchema] = {}
        for name, output_data in data.get("outputs", {}).items():
            output_type_name: str = output_data["type"]
            if output_type_name not in type_mapping:
                raise ValueError(f"Unsupported output type: {output_type_name}")
            output_type: type = type_mapping[output_type_name]
            outputs[name] = OutputSchema(
                name=name,
                type=output_type,
                description=output_data.get("description", ""),
            )

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            parameters=parameters,
            outputs=outputs,
            aliases=data.get("aliases", []),
            metadata=IndicatorMetadata.from_dict(data.get("metadata", {})),
            output_metadata=data.get("output_metadata", {}),
            parameter_aliases=data.get("parameter_aliases", {}),
        )


@dataclass(frozen=True)
class IndicatorMetadata:
    """Additional metadata used by planners/requirements."""

    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()
    lookback_params: tuple[str, ...] = ()
    default_lookback: int | None = None
    input_field: str | None = None  # Default input field (e.g., 'close', 'volume')
    input_series_param: str | None = None  # Parameter name that can override input (e.g., 'input_series')

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "lookback_params": list(self.lookback_params),
            "default_lookback": self.default_lookback,
            "input_field": self.input_field,
            "input_series_param": self.input_series_param,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndicatorMetadata:
        if not data:
            return cls()
        return cls(
            required_fields=tuple(data.get("required_fields", ())),
            optional_fields=tuple(data.get("optional_fields", ())),
            lookback_params=tuple(data.get("lookback_params", ())),
            default_lookback=data.get("default_lookback"),
            input_field=data.get("input_field"),
            input_series_param=data.get("input_series_param"),
        )


# -----------------------------------------------------------------------------
# Conversion between IndicatorSpec and legacy IndicatorSchema
# -----------------------------------------------------------------------------


def indicator_spec_to_schema(spec: IndicatorSpec) -> IndicatorSchema:
    """Derive legacy IndicatorSchema from IndicatorSpec."""
    parameters: dict[str, ParamSchema] = {}
    for name, param in spec.params.items():
        parameters[name] = ParamSchema(
            name=param.name,
            type=param.type,
            default=param.default,
            required=param.required,
            description=param.description,
            valid_values=param.valid_values,
        )

    outputs: dict[str, OutputSchema] = {}
    output_metadata: dict[str, dict[str, Any]] = {}
    for name, out in spec.outputs.items():
        outputs[name] = OutputSchema(
            name=out.name,
            type=out.type,
            description=out.description,
        )
        meta: dict[str, Any] = {"type": out.type.__name__.lower(), "role": out.role}
        if out.polarity is not None:
            meta["polarity"] = out.polarity
        output_metadata[name] = meta

    # Merge semantics with input slots for metadata
    meta = spec.semantics
    input_field = meta.input_field
    input_series_param = meta.input_series_param
    if spec.inputs and not input_field:
        first = spec.inputs[0]
        input_field = first.default_field
        input_series_param = input_series_param or first.name
    metadata = IndicatorMetadata(
        required_fields=meta.required_fields,
        optional_fields=meta.optional_fields,
        lookback_params=meta.lookback_params,
        default_lookback=meta.default_lookback,
        input_field=input_field,
        input_series_param=input_series_param,
    )

    return IndicatorSchema(
        name=spec.name,
        description=spec.description,
        parameters=parameters,
        outputs=outputs,
        aliases=list(spec.aliases),
        metadata=metadata,
        output_metadata=output_metadata,
        parameter_aliases=dict(spec.param_aliases),
    )


def schema_to_indicator_spec(schema: IndicatorSchema) -> IndicatorSpec:
    """Build IndicatorSpec from existing IndicatorSchema (for migration)."""
    params: dict[str, ParamSpec] = {}
    for name, param in schema.parameters.items():
        params[name] = ParamSpec(
            name=param.name,
            type=param.type,
            default=param.default,
            required=param.required,
            description=param.description,
            valid_values=param.valid_values,
            min_value=None,
            max_value=None,
        )

    outputs: dict[str, OutputSpec] = {}
    for name, out in schema.outputs.items():
        meta = schema.output_metadata.get(name, {})
        outputs[name] = OutputSpec(
            name=out.name,
            type=out.type,
            description=out.description,
            role=str(meta.get("role", "line")),
            polarity=meta.get("polarity"),
        )

    semantics = SemanticsSpec(
        required_fields=schema.metadata.required_fields,
        optional_fields=schema.metadata.optional_fields,
        lookback_params=schema.metadata.lookback_params,
        default_lookback=schema.metadata.default_lookback,
        input_field=schema.metadata.input_field,
        input_series_param=schema.metadata.input_series_param,
    )

    inputs: tuple[InputSlotSpec, ...] = ()
    if schema.metadata.input_field or schema.metadata.input_series_param:
        slot_name = schema.metadata.input_series_param or "input_series"
        inputs = (
            InputSlotSpec(
                name=slot_name,
                description="Input series override",
                required=False,
                default_source="ohlcv",
                default_field=schema.metadata.input_field,
            ),
        )

    runtime_binding = RuntimeBindingSpec(kernel_id=schema.name)

    return IndicatorSpec(
        name=schema.name,
        description=schema.description,
        inputs=inputs,
        params=params,
        outputs=outputs,
        semantics=semantics,
        runtime_binding=runtime_binding,
        constraints=(),
        aliases=tuple(schema.aliases),
        param_aliases=dict(schema.parameter_aliases),
    )
