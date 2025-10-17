"""Technical indicators package."""

# Import all indicators to trigger @register decorators
from . import momentum, primitives, trend, volatility, volume  # noqa: F401

__all__ = ["momentum", "trend", "volatility", "volume", "primitives"]
