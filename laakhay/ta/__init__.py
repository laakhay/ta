from .core import Bar, Price, Qty, Rate, Timestamp, dataset
from .dump import to_csv
from .engine import Engine
from .expressions import (
    BinaryOp,
    Expression,
    ExpressionNode,
    Literal,
    UnaryOp,
    as_expression,
)
from .indicators.primitives import cumulative_sum as _cumulative_sum
from .indicators.primitives import diff as _diff
from .indicators.primitives import elementwise_max as _elementwise_max
from .indicators.primitives import elementwise_min as _elementwise_min
from .indicators.primitives import negative_values as _negative_values
from .indicators.primitives import positive_values as _positive_values
from .indicators.primitives import rolling_max as _rolling_max

# Import primitives and create wrapper functions
from .indicators.primitives import rolling_mean as _rolling_mean
from .indicators.primitives import rolling_min as _rolling_min
from .indicators.primitives import rolling_std as _rolling_std
from .indicators.primitives import rolling_sum as _rolling_sum
from .indicators.primitives import shift as _shift
from .load import from_csv
from .public_api import IndicatorHandle, TASeries, indicator, ta
from .registry import (
    IndicatorSchema,
    OutputSchema,
    ParamSchema,
    SeriesContext,
    describe_indicator,
    list_all_names,
    list_indicators,
    register,
)


# Create wrapper functions that can be called directly
def rolling_mean(period: int):
    """Create a rolling mean indicator."""
    return indicator("rolling_mean", period=period)

def rolling_sum(period: int):
    """Create a rolling sum indicator."""
    return indicator("rolling_sum", period=period)

def rolling_max(period: int):
    """Create a rolling max indicator."""
    return indicator("max", period=period)

def rolling_min(period: int):
    """Create a rolling min indicator."""
    return indicator("min", period=period)

def rolling_std(period: int):
    """Create a rolling standard deviation indicator."""
    return indicator("rolling_std", period=period)

def diff():
    """Create a difference indicator."""
    return indicator("diff")

def shift(periods: int):
    """Create a shift indicator."""
    return indicator("shift", periods=periods)

def elementwise_max(other_series):
    """Create an element-wise max indicator."""
    return indicator("elementwise_max", other_series=other_series)

def elementwise_min(other_series):
    """Create an element-wise min indicator."""
    return indicator("elementwise_min", other_series=other_series)

def cumulative_sum():
    """Create a cumulative sum indicator."""
    return indicator("cumulative_sum")

def positive_values():
    """Create a positive values indicator."""
    return indicator("positive_values")

def negative_values():
    """Create a negative values indicator."""
    return indicator("negative_values")

# Import indicators to trigger registration
from . import indicators

__all__ = [
    "Bar",
    "Price",
    "Qty",
    "Rate",
    "Timestamp",
    "dataset",
    "from_csv",
    "to_csv",
    "ParamSchema",
    "OutputSchema",
    "IndicatorSchema",
    "register",
    "indicator",
    "describe_indicator",
    "SeriesContext",
    "list_indicators",
    "list_all_names",
    "Expression",
    "ExpressionNode",
    "BinaryOp",
    "UnaryOp",
    "Literal",
    "as_expression",
    "Engine",
    # New public API
    "ta",
    "IndicatorHandle",
    "TASeries",
    # Primitives
    "rolling_mean",
    "rolling_sum",
    "rolling_max",
    "rolling_min",
    "rolling_std",
    "diff",
    "shift",
    "elementwise_max",
    "elementwise_min",
    "cumulative_sum",
    "positive_values",
    "negative_values",
]
