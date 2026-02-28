from __future__ import annotations

from typing import Any

from .utils import _call_indicator


def bbands(*args: Any, **kwargs: Any):
    return _call_indicator("bbands", args, kwargs, param_order=("period", "std_dev"))


def atr(*args: Any, **kwargs: Any):
    return _call_indicator("atr", args, kwargs, param_order=("period",))


def donchian(*args: Any, **kwargs: Any):
    return _call_indicator("donchian", args, kwargs, param_order=("period",))


def keltner(*args: Any, **kwargs: Any):
    return _call_indicator("keltner", args, kwargs, param_order=("period", "multiplier"))
