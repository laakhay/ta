"""Tests for indicator metadata hints."""

from __future__ import annotations

import pytest

from laakhay.ta import Series, SeriesContext, ta  # ensure registrations
from laakhay.ta.registry import get_global_registry


@pytest.mark.parametrize(
    "name,required_fields,lookback_params,default_lookback",
    [
        ("rolling_mean", ("close",), ("period",), None),
        ("rolling_sum", ("close",), ("period",), None),
        ("rolling_std", ("close",), ("period",), None),
        ("rolling_median", ("close",), ("period",), None),
        ("rolling_ema", ("close",), ("period",), None),
        ("max", ("close",), ("period",), None),
        ("min", ("close",), ("period",), None),
        ("rolling_argmax", ("close",), ("period",), None),
        ("rolling_argmin", ("close",), ("period",), None),
        ("diff", ("close",), (), 2),
        ("shift", ("close",), ("periods",), 1),
        ("cumulative_sum", ("close",), (), 1),
        ("positive_values", ("close",), (), 1),
        ("negative_values", ("close",), (), 1),
        ("sign", ("close",), (), 2),
        ("true_range", ("high", "low", "close"), (), 2),
        ("typical_price", ("high", "low", "close"), (), 1),
        ("sma", ("close",), ("period",), None),
        ("ema", ("close",), ("period",), None),
        ("macd", ("close",), ("fast_period", "slow_period", "signal_period"), 1),
        ("bbands", ("close",), ("period",), None),
        ("rsi", ("close",), ("period",), None),
        ("stochastic", ("high", "low", "close"), ("k_period", "d_period"), None),
        ("atr", ("high", "low", "close"), ("period",), None),
        ("obv", ("close", "volume"), (), 2),
        ("vwap", ("high", "low", "close", "volume"), (), 1),
        ("select", ("close",), (), 1),
        ("swing_points", ("high", "low"), ("left", "right"), None),
    ],
)
def test_indicator_metadata(name, required_fields, lookback_params, default_lookback):
    registry = get_global_registry()
    handle = registry.get(name)
    assert handle is not None, f"Indicator '{name}' not registered"
    metadata = handle.schema.metadata
    assert metadata.required_fields == required_fields
    assert metadata.optional_fields == ()
    assert metadata.lookback_params == lookback_params
    assert metadata.default_lookback == default_lookback


def test_unknown_indicator_metadata_defaults():
    registry = get_global_registry()

    @ta.register("_meta_test_unknown")
    def _meta_test_unknown(ctx: SeriesContext) -> Series:
        return ctx.close

    handle = registry.get("_meta_test_unknown")
    assert handle is not None
    metadata = handle.schema.metadata
    assert metadata.required_fields == ("close",)
    assert metadata.lookback_params == ()
    assert metadata.default_lookback == 1

    registry._indicators.pop("_meta_test_unknown", None)
    registry._aliases.pop("_meta_test_unknown", None)
