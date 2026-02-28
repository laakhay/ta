"""
Event Patterns - Detect state changes and transitions in price/indicator series.

Event patterns return boolean series indicating when specific events occur.
They are composable and can be combined with logical operators (and/or).
"""

from .channel import enter, exit, in_channel, out
from .crossing import cross, crossdown, crossup
from .trend import falling, falling_pct, rising, rising_pct

__all__ = [
    # Crossing patterns
    "crossup",
    "crossdown",
    "cross",
    # Channel patterns
    "in_channel",
    "out",
    "enter",
    "exit",
    # Trend patterns
    "rising",
    "falling",
    "rising_pct",
    "falling_pct",
]
