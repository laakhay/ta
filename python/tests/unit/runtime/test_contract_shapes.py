from __future__ import annotations

import pytest

from laakhay.ta.runtime.contracts import RuntimeSeriesF64, TaStatusCode


def test_runtime_series_shape_validation() -> None:
    series = RuntimeSeriesF64(values=(1.0, 2.0), availability_mask=(True, False))
    assert series.length == 2


def test_runtime_series_shape_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="identical lengths"):
        RuntimeSeriesF64(values=(1.0,), availability_mask=(True, False))


def test_status_code_constants_are_stable() -> None:
    assert int(TaStatusCode.OK) == 0
    assert int(TaStatusCode.INVALID_INPUT) == 1
    assert int(TaStatusCode.SHAPE_MISMATCH) == 2
    assert int(TaStatusCode.INTERNAL_ERROR) == 255
