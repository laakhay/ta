"""Public API for laakhay-ta - clean, vision-aligned interface."""

from __future__ import annotations

from typing import Any, Dict, Union
from decimal import Decimal

from .core import Series, Dataset
from .core.types import Price
from .expressions import Expression, as_expression
from .expressions.models import Literal, BinaryOp, UnaryOp, OperatorType, ExpressionNode
from .registry.models import SeriesContext
from .registry.registry import get_global_registry

# Import indicators to trigger registration
from . import indicators

# Ensure indicators are registered by accessing the registry
from .registry.registry import get_global_registry
_ = get_global_registry()  # This will trigger registration if not already done


class IndicatorHandle:
    """Handle for an indicator that can be called and composed algebraically.
    
    This enables the clean API shown in the vision:
    - sma_fast = ta.indicator("sma", period=20)
    - spread = sma_fast - sma_slow
    - result = sma_fast(dataset)
    """
    
    def __init__(self, name: str, **params: Any):
        self.name = name
        self.params: Dict[str, Any] = params
        
        # Ensure indicators are registered before accessing registry
        from . import indicators  # noqa: F401
        
        self._registry = get_global_registry()
        
        # If indicator not found, try to re-register indicators
        if name not in self._registry._indicators:
            # Force re-import of all indicator modules to trigger registration
            import importlib
            import sys
            
            # Re-import all indicator modules
            for module_name in list(sys.modules.keys()):
                if module_name.startswith('laakhay.ta.indicators.') and module_name != 'laakhay.ta.indicators.__init__':
                    importlib.reload(sys.modules[module_name])
            
            # Check again
            if name not in self._registry._indicators:
                raise ValueError(f"Indicator '{name}' not found in registry")
        
        self._indicator_func = self._registry._indicators[name]
        self._schema = self._get_schema()
    
    def _get_schema(self) -> Dict[str, Any]:
        """Get indicator schema for introspection."""
        # For now, return basic info. In the future, this could be more detailed
        return {
            'name': self.name,
            'params': self.params,
            'description': getattr(self._indicator_func, '__doc__', 'No description available')
        }
    
    def __call__(self, dataset: Union[Dataset, Series[Price]]) -> Series[Price]:
        """Call the indicator with a dataset or series.
        
        Args:
            dataset: Dataset or Series to evaluate the indicator on
            
        Returns:
            Series with indicator values
        """
        if isinstance(dataset, Series):
            # Single series - create context
            ctx = SeriesContext(close=dataset)
        else:
            # Dataset - extract primary series
            ctx = dataset.to_context()
        
        return self._indicator_func(ctx, **self.params)
    
    def _to_expression(self) -> Expression:
        """Convert this handle to an expression for algebraic composition.
        
        This creates a placeholder expression that will be resolved when evaluated.
        """
        # Create a special node that represents this indicator handle
        return Expression(IndicatorNode(self.name, self.params))
    
    # Algebraic operators for composition
    def __add__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.ADD, self._to_expression()._node, other_expr._node))
    
    def __sub__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.SUB, self._to_expression()._node, other_expr._node))
    
    def __mul__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.MUL, self._to_expression()._node, other_expr._node))
    
    def __truediv__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.DIV, self._to_expression()._node, other_expr._node))
    
    def __mod__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.MOD, self._to_expression()._node, other_expr._node))
    
    def __pow__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.POW, self._to_expression()._node, other_expr._node))
    
    def __lt__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.LT, self._to_expression()._node, other_expr._node))
    
    def __gt__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.GT, self._to_expression()._node, other_expr._node))
    
    def __le__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.LE, self._to_expression()._node, other_expr._node))
    
    def __ge__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.GE, self._to_expression()._node, other_expr._node))
    
    def __eq__(self, other: Any) -> Expression:  # type: ignore[override]
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.EQ, self._to_expression()._node, other_expr._node))
    
    def __ne__(self, other: Any) -> Expression:  # type: ignore[override]
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.NE, self._to_expression()._node, other_expr._node))
    
    def __and__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.AND, self._to_expression()._node, other_expr._node))
    
    def __or__(self, other: Any) -> Expression:
        other_expr = _to_expression(other)
        return Expression(BinaryOp(OperatorType.OR, self._to_expression()._node, other_expr._node))
    
    def __invert__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.NOT, self._to_expression()._node))
    
    def __neg__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.NEG, self._to_expression()._node))
    
    def __pos__(self) -> Expression:
        return Expression(UnaryOp(OperatorType.POS, self._to_expression()._node))
    
    @property
    def schema(self):
        """Get the indicator schema for introspection."""
        return self._schema
    
    def describe(self) -> str:
        """Get human-readable description of this indicator handle."""
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({params_str})"


class IndicatorNode(ExpressionNode):
    """Expression node representing an indicator handle.
    
    This allows indicator handles to participate in expression graphs
    while deferring evaluation until the expression is resolved.
    """
    
    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params
        self._registry = get_global_registry()
    
    def evaluate(self, context: Dict[str, Series[Any]]) -> Series[Any]:
        """Evaluate this indicator node with the given context."""
        if self.name not in self._registry._indicators:
            raise ValueError(f"Indicator '{self.name}' not found in registry")
        
        indicator_func = self._registry._indicators[self.name]
        return indicator_func(SeriesContext(**context), **self.params)
    
    def dependencies(self) -> list[str]:
        """Get dependencies for this indicator."""
        # For now, return empty list. In the future, this could analyze
        # the indicator function to determine its dependencies
        return []
    
    def describe(self) -> str:
        """Get human-readable description of this node."""
        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({params_str})"


def _to_expression(value: Union[Expression, IndicatorHandle, Series[Any], float, int, Decimal]) -> Expression:
    """Convert a value to an Expression for algebraic composition."""
    if isinstance(value, Expression):
        return value
    elif isinstance(value, IndicatorHandle):
        return value._to_expression()
    elif isinstance(value, Series):
        return as_expression(value)
    else:
        # Convert Decimal to float for Literal
        if isinstance(value, Decimal):
            value = float(value)
        return Expression(Literal(value))


def indicator(name: str, **params: Any) -> IndicatorHandle:
    """Create an indicator handle.
    
    Args:
        name: Name of the indicator (e.g., 'sma', 'rsi', 'ema')
        **params: Parameters for the indicator
        
    Returns:
        IndicatorHandle that can be called and composed algebraically
        
    Examples:
        >>> sma_fast = ta.indicator("sma", period=20)
        >>> rsi = ta.indicator("rsi", period=14)
        >>> spread = sma_fast - sma_slow
        >>> result = sma_fast(dataset)
    """
    return IndicatorHandle(name, **params)


def literal(value: Union[float, int, Decimal]) -> Expression:
    """Create a literal expression.
    
    Args:
        value: Literal value (number)
        
    Returns:
        Expression containing the literal value
        
    Examples:
        >>> bias = ta.literal(15)
        >>> signal = (spread + bias) > 100
    """
    return Expression(Literal(value))


# Main API namespace
class TANamespace:
    """Main API namespace for laakhay-ta."""
    
    def __init__(self):
        self.indicator = indicator
        self.literal = literal
    
    def __call__(self, series: Series[Price], **additional_series: Series[Any]) -> TASeries:
        """Create a technical analysis context for a series.
        
        This provides the alternative API: ta(close_series).sma(20)
        """
        return TASeries(series, **additional_series)


class TASeries:
    """Smart wrapper that provides seamless indicator access on series.
    
    This enables the alternative API: ta(close_series).sma(20)
    """
    
    def __init__(self, series: Series[Price], **additional_series: Series[Any]):
        self._primary_series = series
        self._additional_series = additional_series
        self._context = SeriesContext(close=series, **additional_series)
        self._registry = get_global_registry()
    
    def __getattr__(self, name: str) -> Any:
        """Dynamic indicator access."""
        # Ensure indicators are registered before accessing registry
        from . import indicators  # noqa: F401
        
        # If indicator not found, try to re-register indicators
        if name not in self._registry._indicators:
            # Force re-import of all indicator modules to trigger registration
            import importlib
            import sys
            
            # Re-import all indicator modules
            for module_name in list(sys.modules.keys()):
                if module_name.startswith('laakhay.ta.indicators.') and module_name != 'laakhay.ta.indicators.__init__':
                    importlib.reload(sys.modules[module_name])
        
        if name in self._registry._indicators:
            indicator_func = self._registry._indicators[name]
            def indicator_wrapper(*args, **kwargs):
                # Return an expression that can be used in algebraic operations
                result = indicator_func(self._context, *args, **kwargs)
                return as_expression(result)
            return indicator_wrapper
        raise AttributeError(f"Indicator '{name}' not found")
    
    # Algebraic operators delegate to expression system
    def __add__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) + other
    
    def __sub__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) - other
    
    def __mul__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) * other
    
    def __truediv__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) / other
    
    def __mod__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) % other
    
    def __pow__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) ** other
    
    def __lt__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) < other
    
    def __gt__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) > other
    
    def __le__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) <= other
    
    def __ge__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) >= other
    
    def __eq__(self, other: Any) -> Expression:  # type: ignore[override]
        return as_expression(self._primary_series) == other
    
    def __ne__(self, other: Any) -> Expression:  # type: ignore[override]
        return as_expression(self._primary_series) != other
    
    def __and__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) & other
    
    def __or__(self, other: Any) -> Expression:
        return as_expression(self._primary_series) | other
    
    def __invert__(self) -> Expression:
        return ~as_expression(self._primary_series)
    
    def __neg__(self) -> Expression:
        return -as_expression(self._primary_series)
    
    def __pos__(self) -> Expression:
        return +as_expression(self._primary_series)


# Create the main API instance
ta = TANamespace()
