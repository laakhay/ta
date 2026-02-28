from __future__ import annotations

from typing import Any

from .utils import _call_indicator


def obv(*args: Any, **kwargs: Any):
    return _call_indicator("obv", args, kwargs)


def vwap(*args: Any, **kwargs: Any):
    return _call_indicator("vwap", args, kwargs)


def cmf(*args: Any, **kwargs: Any):
    return _call_indicator("cmf", args, kwargs, param_order=("period",))


def klinger(*args: Any, **kwargs: Any):
    return _call_indicator("klinger", args, kwargs, param_order=("fast_period", "slow_period", "signal_period"))
