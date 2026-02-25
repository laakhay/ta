from __future__ import annotations

from typing import Any

from .utils import _call_indicator


def sma(*args: Any, **kwargs: Any):
    return _call_indicator("sma", args, kwargs, param_order=("period",))


def ema(*args: Any, **kwargs: Any):
    return _call_indicator("ema", args, kwargs, param_order=("period",))


def ichimoku(*args: Any, **kwargs: Any):
    return _call_indicator(
        "ichimoku", args, kwargs, param_order=("tenkan_period", "kijun_period", "senkou_b_period", "displacement")
    )


def supertrend(*args: Any, **kwargs: Any):
    return _call_indicator("supertrend", args, kwargs, param_order=("period", "multiplier"))


def psar(*args: Any, **kwargs: Any):
    return _call_indicator("psar", args, kwargs, param_order=("step", "max_step"))


def hma(*args: Any, **kwargs: Any):
    return _call_indicator("hma", args, kwargs, param_order=("period",))


def wma(*args: Any, **kwargs: Any):
    return _call_indicator("wma", args, kwargs, param_order=("period",))


def elder_ray(*args: Any, **kwargs: Any):
    return _call_indicator("elder_ray", args, kwargs, param_order=("period",))


def fisher(*args: Any, **kwargs: Any):
    return _call_indicator("fisher", args, kwargs, param_order=("period",))


def swing_high_at(*args: Any, **kwargs: Any):
    return _call_indicator("swing_high_at", args, kwargs, param_order=("index", "left", "right"))


def swing_low_at(*args: Any, **kwargs: Any):
    return _call_indicator("swing_low_at", args, kwargs, param_order=("index", "left", "right"))


def fib_level_down(*args: Any, **kwargs: Any):
    return _call_indicator("fib_level_down", args, kwargs, param_order=("level", "left", "right", "leg"))


def fib_level_up(*args: Any, **kwargs: Any):
    return _call_indicator("fib_level_up", args, kwargs, param_order=("level", "left", "right", "leg"))


def fib_anchor_high(*args: Any, **kwargs: Any):
    return _call_indicator("fib_anchor_high", args, kwargs, param_order=("left", "right", "leg"))


def fib_anchor_low(*args: Any, **kwargs: Any):
    return _call_indicator("fib_anchor_low", args, kwargs, param_order=("left", "right", "leg"))
