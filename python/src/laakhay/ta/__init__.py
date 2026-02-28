"""Laakhay TA: Technical analysis and expression engine.

Public API (primary entry points):
- dataset: Build datasets (dataset(), dataset_from_bars(), trim_dataset)
- ta: Strategy expression builder (e.g., ta.sma(20), ta.ohlcv("close"))
- indicator, literal, Expression: Programmatic expression construction
- sma, ema, macd, rsi, atr, ...: Indicator shortcuts for functional use
- Series, Bar, Price: Core types
- validate, preview, analyze: Expression validation and evaluation (via expr)
- Engine: Batch expression evaluation

See laakhay.ta.api for full API surface.
"""

from .api import *  # noqa: F401,F403
from .api import __all__ as _api_all
from .runtime import RuntimeBackend, get_runtime_backend, is_rust_backend

__all__ = list(_api_all) + ["RuntimeBackend", "get_runtime_backend", "is_rust_backend"]
