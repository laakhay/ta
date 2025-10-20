"""Schema dataclasses for indicator metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ParamSchema:
    """Schema definition for an indicator parameter."""
    
    name: str
    type: type
    default: Optional[Any] = None
    required: bool = True
    description: str = ""
    valid_values: Optional[list[Any]] = None
    
    def __post_init__(self) -> None:
        """Validate parameter schema."""
        if self.required and self.default is not None:
            raise ValueError("Required parameters cannot have default values")
        if not self.required and self.default is None:
            raise ValueError("Optional parameters must have default values")


@dataclass(frozen=True)
class OutputSchema:
    """Schema definition for an indicator output."""
    
    name: str
    type: type
    description: str = ""


@dataclass(frozen=True)
class IndicatorSchema:
    """Complete schema for an indicator."""
    
    name: str
    description: str = ""
    parameters: dict[str, ParamSchema] = field(default_factory=dict)
    outputs: dict[str, OutputSchema] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    
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
        }
        
        parameters: dict[str, ParamSchema] = {}
        for name, param_data in data.get("parameters", {}).items():
            param_type = type_mapping.get(param_data["type"], type(None))
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
            output_type = type_mapping.get(output_data["type"], type(None))
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
        )
