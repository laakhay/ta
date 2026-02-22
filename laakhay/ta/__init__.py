"""Laakhay TA: Technical analysis and expression engine.

Public API (primary entry points):
- dataset: Build datasets from CSV, bars, or other sources
- ta: Strategy expression builder (e.g., ta.sma(20), ta.ohlcv("close"))
- indicator, literal, Expression: Programmatic expression construction
- sma, ema, macd, rsi, atr, ...: Indicator shortcuts for functional use
- Series, Bar, Price: Core types
- validate, preview, analyze: Expression validation and evaluation (via expr)
- Engine: Batch expression evaluation

See laakhay.ta.api for full API surface.
"""

import importlib

from .api import *  # noqa: F401,F403
from .api import __all__ as _api_all
from .core.dataset import dataset as _dataset_builder

_dataset_module = importlib.import_module(".data.dataset", __name__)


class _DatasetAccessor:
    def __init__(self, module):
        self._module = module

    def __call__(self, *args, **kwargs):
        return _dataset_builder(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._module, attr)


dataset = _DatasetAccessor(_dataset_module)
__all__ = list(_api_all) + ["dataset"]
