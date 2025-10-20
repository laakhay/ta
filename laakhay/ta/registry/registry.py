"""Indicator registry implementation."""

from __future__ import annotations

import inspect
import threading
from typing import Any, Callable, Dict, List, Optional, Union

from .models import IndicatorHandle, SeriesContext
from .schemas import ParamSchema, OutputSchema, IndicatorSchema
from ..core import Series


class Registry:
    """Registry for managing indicators."""
    
    def __init__(self) -> None:
        """Initialize empty registry."""
        self._indicators: Dict[str, IndicatorHandle] = {}
        self._aliases: Dict[str, str] = {}  # alias -> name mapping
        self._lock = threading.RLock()  # Reentrant lock for thread safety
    
    def register(
        self, 
        func: Callable[..., Any], 
        name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Callable[..., Any]:
        """Register an indicator function."""
        with self._lock:
            # Use function name if no name provided
            if name is None:
                name = func.__name__
            
            # Validate function signature and return type
            self._validate_function(func)
            
            # Build schema from function signature and docstring
            schema = self._build_schema(func, name, description or func.__doc__ or "")
            
            # Create handle
            handle = IndicatorHandle(
                name=name,
                func=func,
                signature=inspect.signature(func),
                schema=schema,
                aliases=aliases or []
            )
            
            # Register main name
            self._indicators[name] = handle
            
            # Register aliases
            for alias in handle.aliases:
                if alias in self._indicators:
                    raise ValueError(f"Alias '{alias}' conflicts with existing indicator '{alias}'")
                self._aliases[alias] = name
            
            return func
    
    def get(self, name: str) -> Optional[IndicatorHandle]:
        """Get indicator by name or alias."""
        with self._lock:
            # Check direct name first
            if name in self._indicators:
                return self._indicators[name]
            
            # Check aliases
            if name in self._aliases:
                actual_name = self._aliases[name]
                return self._indicators[actual_name]
            
            return None
    
    def list_indicators(self) -> List[str]:
        """List all registered indicator names."""
        with self._lock:
            return list(self._indicators.keys())
    
    def list_all_names(self) -> List[str]:
        """List all registered indicator names and aliases."""
        with self._lock:
            names = list(self._indicators.keys())
            aliases = list(self._aliases.keys())
            return sorted(names + aliases)
    
    def clear(self) -> None:
        """Clear all registered indicators. Useful for testing."""
        with self._lock:
            self._indicators.clear()
            self._aliases.clear()
    
    def _validate_function(self, func: Callable[..., Any]) -> None:
        """Validate that a function is suitable for registration as an indicator."""
        sig = inspect.signature(func)
        
        # Check if function has at least one parameter (SeriesContext)
        if len(sig.parameters) == 0:
            raise ValueError(f"Indicator function '{func.__name__}' must have at least one parameter (SeriesContext)")
        
        # Check first parameter is SeriesContext
        first_param = list(sig.parameters.values())[0]
        if first_param.annotation == inspect.Parameter.empty:
            # If no annotation, we'll allow it but warn
            pass
        elif first_param.annotation != SeriesContext and not (
            hasattr(first_param.annotation, '__name__') and 
            first_param.annotation.__name__ == 'SeriesContext'
        ) and first_param.annotation != 'SeriesContext':
            raise ValueError(f"Indicator function '{func.__name__}' first parameter must be SeriesContext, got {first_param.annotation}")
        
        # Check return type annotation
        return_annotation = sig.return_annotation
        if return_annotation != inspect.Signature.empty:
            # Check if return type is Series, tuple, or dict (for multi-output)
            if hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is Series:
                # Series[SomeType] - this is good
                pass
            elif return_annotation == Series:
                # Just Series - this is also good
                pass
            elif isinstance(return_annotation, str) and return_annotation.startswith('Series['):
                # String annotation like "Series[Price]" - this is good
                pass
            elif isinstance(return_annotation, str) and return_annotation.startswith('Tuple['):
                # String annotation like "Tuple[Series[Price], ...]" - this is good
                pass
            elif hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is tuple:
                # Tuple return type for multi-output indicators - this is good
                pass
            elif hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is dict:
                # Dict return type for named outputs - this is good
                pass
            else:
                raise ValueError(f"Indicator function '{func.__name__}' must return Series[SomeType], Tuple, or Dict, got {return_annotation}")
        else:
            # No return annotation - we'll allow it but it's not ideal
            pass
    
    def _build_schema(
        self, 
        func: Callable[..., Any], 
        name: str, 
        description: str
    ) -> IndicatorSchema:
        """Build schema from function signature."""
        sig = inspect.signature(func)
        parameters = {}
        
        # Skip first parameter if it's SeriesContext
        param_items = list(sig.parameters.items())
        if param_items and param_items[0][1].annotation == SeriesContext:
            param_items = param_items[1:]  # Skip the first parameter
        elif param_items and hasattr(param_items[0][1].annotation, '__name__') and param_items[0][1].annotation.__name__ == 'SeriesContext':
            param_items = param_items[1:]  # Skip the first parameter
        
        # Process remaining parameters
        for param_name, param in param_items:
            param_type = self._get_param_type(param.annotation)
            has_default = param.default != inspect.Parameter.empty
            default = param.default if has_default else None

            # Determine required flag without forcing Optional[T]=None to required.
            required = not has_default

            parameters[param_name] = ParamSchema(
                name=param_name,
                type=param_type,  # type: ignore[arg-type]
                default=default,
                required=required,
                description=f"Parameter {param_name}"
            )
        
        # Build output schema based on return type annotation
        outputs = self._build_output_schema(func)
        
        return IndicatorSchema(
            name=name,
            description=description.strip(),
            parameters=parameters,  # type: ignore[arg-type]
            outputs=outputs
        )
    
    def _get_param_type(self, annotation: Any) -> type:
        """Convert annotation to type with support for complex types."""
        if annotation == inspect.Parameter.empty:
            return Any  # type: ignore[return-value]
        if isinstance(annotation, type):
            return annotation  # type: ignore[return-value]

        # Handle typing annotations
        origin = getattr(annotation, '__origin__', None)
        args = getattr(annotation, '__args__', ())
        
        # Handle basic types
        if origin is int:
            return int  # type: ignore[return-value]
        elif origin is float:
            return float  # type: ignore[return-value]
        elif origin is str:
            return str  # type: ignore[return-value]
        elif origin is bool:
            return bool  # type: ignore[return-value]
        elif origin is list:
            return list  # type: ignore[return-value]
        elif origin is dict:
            return dict  # type: ignore[return-value]
        
        # Handle Union types (e.g., Union[int, float])
        elif origin is Union:
            non_none_types = [arg for arg in args if arg is not type(None)]
            if not non_none_types:
                return Any  # Only None specified
            if len(non_none_types) == 1:
                return self._get_param_type(non_none_types[0])
            # For multiple concrete types, return the first non-None type
            return self._get_param_type(non_none_types[0])
        
        # Handle Optional types (Union[T, None])
        elif str(annotation).startswith('typing.Union') and len(args) == 2 and type(None) in args:
            non_none_arg = args[0] if args[1] is type(None) else args[1]
            return self._get_param_type(non_none_arg)
        
        # Handle generic types like Series[Price]
        elif hasattr(annotation, '__origin__') and hasattr(annotation, '__args__'):
            # For complex generics, we'll store the full annotation for future use
            # but return the base type for schema compatibility
            base_type = getattr(annotation, '__origin__', annotation)
            if base_type is not None and isinstance(base_type, type):
                return base_type  # type: ignore[return-value]
        
        return Any  # type: ignore[return-value]
    
    def _build_output_schema(self, func: Callable[..., Any]) -> Dict[str, OutputSchema]:
        """Build output schema based on function return type annotation."""
        sig = inspect.signature(func)
        return_annotation = sig.return_annotation
        
        # Default single output for unannotated functions
        if return_annotation == inspect.Signature.empty:
            return {
                "result": OutputSchema(
                    name="result",
                    type=Series,  # Assume Series output
                    description="Indicator output series"
                )
            }
        
        # Handle Series[SomeType] - single output
        if hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is Series:
            return {
                "result": OutputSchema(
                    name="result",
                    type=Series,
                    description="Indicator output series"
                )
            }
        
        # Handle plain Series type
        if return_annotation == Series:
            return {
                "result": OutputSchema(
                    name="result",
                    type=Series,
                    description="Indicator output series"
                )
            }
        
        # Handle tuple return types for multi-output indicators
        if hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is tuple:
            args = getattr(return_annotation, '__args__', ())
            outputs = {}
            for i, arg_type in enumerate(args):
                output_name = f"output_{i}" if len(args) > 1 else "result"
                if hasattr(arg_type, '__origin__') and arg_type.__origin__ is Series:
                    schema_type = Series
                else:
                    schema_type = arg_type if isinstance(arg_type, type) else Any  # type: ignore[misc]
                
                outputs[output_name] = OutputSchema(
                    name=output_name,
                    type=schema_type,  # type: ignore[arg-type]
                    description=f"Indicator output {i + 1}"
                )
            return outputs  # type: ignore[return-value]
        
        # Handle dict return types for named outputs
        if hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is dict:
            # For Dict[str, Series[SomeType]], we can't extract the key names at runtime
            # So we'll provide a generic output
            return {
                "result": OutputSchema(
                    name="result",
                    type=dict,
                    description="Indicator output dictionary"
                )
            }
        
        # Fallback for unknown return types
        return {
            "result": OutputSchema(
                name="result",
                type=type(None),  # Unknown type
                description="Indicator output"
            )
        }


# Global registry instance
_global_registry = Registry()


def get_global_registry() -> Registry:
    """Get the global registry instance. Useful for testing and advanced usage."""
    return _global_registry


def register(
    name: Optional[str] = None,
    aliases: Optional[List[str]] = None,
    description: Optional[str] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register an indicator function."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return _global_registry.register(func, name, aliases, description)
    return decorator


def indicator(name: str, **overrides: Any) -> IndicatorHandle:
    """Get indicator handle by name with optional parameter overrides."""
    handle = _global_registry.get(name)
    if handle is None:
        raise ValueError(f"Indicator '{name}' not found")
    return handle.with_overrides(**overrides)


def describe_indicator(name: str) -> IndicatorSchema:
    """Get indicator schema by name."""
    handle = _global_registry.get(name)
    if handle is None:
        raise ValueError(f"Indicator '{name}' not found")
    return handle.schema


def list_indicators() -> List[str]:
    """List all registered indicator names."""
    return _global_registry.list_indicators()


def list_all_names() -> List[str]:
    """List all registered indicator names and aliases."""
    return _global_registry.list_all_names()
