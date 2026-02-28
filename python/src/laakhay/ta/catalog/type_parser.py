"""Type parsing and classification utilities."""

from __future__ import annotations

from types import UnionType
from typing import (
    Any,
    Literal,
    Union,
    cast,
    get_args,
    get_origin,
)

from .utils import jsonify_value

ParamType = str

_SIMPLE_TYPE_MAP: dict[Any, ParamType] = {
    int: "int",
    float: "float",
    str: "string",
    bool: "bool",
}


class TypeParser:
    """Parses and classifies Python type annotations for indicator parameters."""

    def __init__(self) -> None:
        """Initialize type parser."""
        pass

    def classify_parameter(self, name: str, annotation: Any, default: Any) -> dict[str, Any]:
        """
        Classify a parameter from its type annotation.

        Args:
            name: Parameter name
            annotation: Type annotation
            default: Default value

        Returns:
            Dictionary with parameter classification:
            - param_type: str (int, float, string, bool, enum, json)
            - required: bool
            - collection: bool
            - collection_python_type: type | None
            - item_type: str | None
            - item_python_type: Any | None
            - options: list[Any] | None (for enum types)
            - supported: bool
        """
        import inspect

        required = default is inspect.Parameter.empty
        python_default = None if required else default
        public_default = jsonify_value(python_default)

        if annotation is inspect.Parameter.empty:
            annotation = Any

        annotation, optional = self._strip_optional(annotation)
        required = required and not optional

        param_type = self._resolve_param_type(annotation)
        options: list[Any] | None = None
        collection = False
        collection_python_type: type | None = None
        item_type: ParamType | None = None
        item_python_type: Any | None = None
        supported = True

        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is list or origin is list.__class__:
            collection = True
            collection_python_type = list
            if args:
                item_type, item_python_type = self._resolve_simple_type(args[0])
        elif origin is tuple:
            collection = True
            collection_python_type = tuple
            if args:
                first = args[0]
                if first is Ellipsis and len(args) > 1:
                    first = args[1]
                item_type, item_python_type = self._resolve_simple_type(first)
        elif origin is None and isinstance(annotation, str):
            param_type = param_type or "json"
        elif self._is_literal(annotation):
            literal_args = cast(tuple[Any, ...], get_args(annotation) or ())
            options = [jsonify_value(arg) for arg in literal_args]
            item_type = None
            item_python_type = None
            param_type = "enum"

        if param_type is None:
            param_type = "json"

        if item_type is None and collection:
            item_type = param_type
            item_python_type = annotation

        if self._is_series_type(annotation):
            supported = False

        return {
            "name": name,
            "param_type": param_type,
            "required": required,
            "python_type": annotation,
            "default_value": python_default,
            "public_default": public_default,
            "options": options,
            "collection": collection,
            "collection_python_type": collection_python_type,
            "item_type": item_type,
            "item_python_type": item_python_type,
            "supported": supported,
        }

    def _strip_optional(self, annotation: Any) -> tuple[Any, bool]:
        """Strip Optional/Union[..., None] wrapper."""
        origin = get_origin(annotation)
        if origin in (Union, UnionType):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) == 1:
                return args[0], True
        return annotation, False

    def _resolve_simple_type(self, annotation: Any) -> tuple[ParamType, Any]:
        """Resolve simple type from annotation."""
        annotation, _ = self._strip_optional(annotation)
        origin = get_origin(annotation)
        if origin in (Union, UnionType):
            for arg in get_args(annotation):
                if arg is type(None):
                    continue
                simple, python = self._resolve_simple_type(arg)
                if simple:
                    return simple, python
        param_type = self._resolve_param_type(annotation) or "json"
        return param_type, annotation

    def _resolve_param_type(self, annotation: Any) -> ParamType | None:
        """Resolve parameter type string from annotation."""
        if annotation in _SIMPLE_TYPE_MAP:
            return _SIMPLE_TYPE_MAP[annotation]
        if isinstance(annotation, type) and annotation in _SIMPLE_TYPE_MAP:
            return _SIMPLE_TYPE_MAP[annotation]
        if isinstance(annotation, str):
            normalized = annotation.lower()
            if normalized in {"int", "float", "str", "string", "bool"}:
                mapping = {"str": "string", "string": "string"}
                return cast(ParamType, mapping.get(normalized, normalized))
        if self._is_literal(annotation):
            return "enum"
        origin = get_origin(annotation)
        if origin in {list, tuple}:
            return "json"
        return None

    @staticmethod
    def _is_literal(annotation: Any) -> bool:
        """Check if annotation is a Literal type."""
        return get_origin(annotation) is Literal

    @staticmethod
    def _is_series_type(annotation: Any) -> bool:
        """Check if annotation is a Series type."""
        text = str(annotation)
        return "Series" in text and "SeriesContext" not in text


def classify_parameter_type(annotation: Any, default: Any = None) -> dict[str, Any]:
    """Convenience function to classify a parameter type.

    Args:
        annotation: Type annotation
        default: Default value

    Returns:
        Dictionary with parameter classification
    """
    parser = TypeParser()
    return parser.classify_parameter("param", annotation, default)
