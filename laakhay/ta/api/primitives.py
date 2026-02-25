from __future__ import annotations

from typing import Any

from .utils import _call_indicator


def rolling_mean(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_mean", args, kwargs, param_order=("period",))


def rolling_sum(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_sum", args, kwargs, param_order=("period",))


def rolling_max(*args: Any, **kwargs: Any):
    return _call_indicator("max", args, kwargs, param_order=("period",))


def rolling_min(*args: Any, **kwargs: Any):
    return _call_indicator("min", args, kwargs, param_order=("period",))


def rolling_std(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_std", args, kwargs, param_order=("period",))


def diff(*args: Any, **kwargs: Any):
    return _call_indicator("diff", args, kwargs)


def shift(*args: Any, **kwargs: Any):
    return _call_indicator("shift", args, kwargs, param_order=("periods",))


def cumulative_sum(*args: Any, **kwargs: Any):
    return _call_indicator("cumulative_sum", args, kwargs)


def positive_values(*args: Any, **kwargs: Any):
    return _call_indicator("positive_values", args, kwargs)


def negative_values(*args: Any, **kwargs: Any):
    return _call_indicator("negative_values", args, kwargs)


def rolling_ema(*args: Any, **kwargs: Any):
    return _call_indicator("rolling_ema", args, kwargs, param_order=("period",))


def true_range(*args: Any, **kwargs: Any):
    return _call_indicator("true_range", args, kwargs)


def typical_price(*args: Any, **kwargs: Any):
    return _call_indicator("typical_price", args, kwargs)


def sign(*args: Any, **kwargs: Any):
    return _call_indicator("sign", args, kwargs)


def downsample(*args: Any, **kwargs: Any):
    return _call_indicator("downsample", args, kwargs, param_order=("factor",))


def upsample(*args: Any, **kwargs: Any):
    return _call_indicator("upsample", args, kwargs, param_order=("factor",))


def sync_timeframe(*args: Any, **kwargs: Any):
    return _call_indicator("sync_timeframe", args, kwargs)
