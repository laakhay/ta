from __future__ import annotations

from typing import Any

from .utils import _call_indicator


def macd(*args: Any, **kwargs: Any):
    return _call_indicator(
        "macd",
        args,
        kwargs,
        param_order=("fast_period", "slow_period", "signal_period"),
    )


def rsi(*args: Any, **kwargs: Any):
    return _call_indicator("rsi", args, kwargs, param_order=("period",))


def stochastic(*args: Any, **kwargs: Any):
    return _call_indicator("stochastic", args, kwargs, param_order=("k_period", "d_period"))


def adx(*args: Any, **kwargs: Any):
    return _call_indicator("adx", args, kwargs, param_order=("period",))


def ao(*args: Any, **kwargs: Any):
    return _call_indicator("ao", args, kwargs, param_order=("fast_period", "slow_period"))


def cci(*args: Any, **kwargs: Any):
    return _call_indicator("cci", args, kwargs, param_order=("period",))


def cmo(*args: Any, **kwargs: Any):
    return _call_indicator("cmo", args, kwargs, param_order=("period",))


def coppock(*args: Any, **kwargs: Any):
    return _call_indicator("coppock", args, kwargs, param_order=("wma_period", "fast_roc", "slow_roc"))


def mfi(*args: Any, **kwargs: Any):
    return _call_indicator("mfi", args, kwargs, param_order=("period",))


def roc(*args: Any, **kwargs: Any):
    return _call_indicator("roc", args, kwargs, param_order=("period",))


def vortex(*args: Any, **kwargs: Any):
    return _call_indicator("vortex", args, kwargs, param_order=("period",))


def williams_r(*args: Any, **kwargs: Any):
    return _call_indicator("williams_r", args, kwargs, param_order=("period",))
