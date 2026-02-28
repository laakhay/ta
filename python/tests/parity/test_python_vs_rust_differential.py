from __future__ import annotations

import math

import ta_py


def _close(a: float, b: float, tol: float = 1e-9) -> bool:
    if math.isnan(a) and math.isnan(b):
        return True
    return abs(a - b) <= tol


def test_rolling_sum_known_vector():
    out = ta_py.rolling_sum([1.0, 2.0, 3.0, 4.0, 5.0], 3)
    exp = [math.nan, math.nan, 6.0, 9.0, 12.0]
    assert all(_close(float(o), float(e)) for o, e in zip(out, exp, strict=True))


def test_rolling_mean_known_vector():
    out = ta_py.rolling_mean([1.0, 2.0, 3.0, 4.0, 5.0], 3)
    exp = [math.nan, math.nan, 2.0, 3.0, 4.0]
    assert all(_close(float(o), float(e)) for o, e in zip(out, exp, strict=True))


def test_rsi_shape_and_range():
    out = ta_py.rsi([100.0, 101.0, 103.0, 102.0, 104.0, 105.0], 3)
    assert len(out) == 6
    for x in out:
        if not math.isnan(x):
            assert 0.0 <= x <= 100.0


def test_atr_from_tr_shape():
    out = ta_py.atr_from_tr([1.0, 2.0, 2.0, 3.0, 4.0], 3)
    assert len(out) == 5
    assert math.isnan(out[0]) and math.isnan(out[1])
    assert not math.isnan(out[2])
