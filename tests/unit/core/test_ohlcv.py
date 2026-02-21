"""Tests for OHLCV and Bar."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

UTC = UTC
from decimal import Decimal
from typing import Any

import pytest

from laakhay.ta.core import OHLCV
from laakhay.ta.core.bar import Bar
from laakhay.ta.core.types import Timestamp

UTC = UTC


# ---------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------


def iso(ts: datetime) -> str:
    return ts.isoformat()


def f(x: Decimal | float) -> float:
    return float(x)


@pytest.fixture
def ohlcv(sample_ohlcv_data: dict[str, Any]) -> OHLCV:
    return OHLCV(
        timestamps=sample_ohlcv_data["timestamps"],
        opens=sample_ohlcv_data["opens"],
        highs=sample_ohlcv_data["highs"],
        lows=sample_ohlcv_data["lows"],
        closes=sample_ohlcv_data["closes"],
        volumes=sample_ohlcv_data["volumes"],
        is_closed=sample_ohlcv_data["is_closed"],
        symbol=sample_ohlcv_data["symbol"],
        timeframe=sample_ohlcv_data["timeframe"],
    )


@pytest.fixture
def empty_ohlcv() -> OHLCV:
    return OHLCV(
        timestamps=(),
        opens=(),
        highs=(),
        lows=(),
        closes=(),
        volumes=(),
        is_closed=(),
        symbol="BTCUSDT",
        timeframe="1h",
    )


# ---------------------------------------------------------------------
# Core behavior
# ---------------------------------------------------------------------


class TestOHLCVCore:
    def test_creation_and_empty(self, ohlcv: OHLCV, empty_ohlcv: OHLCV) -> None:
        assert len(ohlcv) == 4 and ohlcv.length == 4 and not ohlcv.is_empty
        assert ohlcv.symbol == "BTCUSDT" and ohlcv.timeframe == "1h"
        assert len(empty_ohlcv) == 0 and empty_ohlcv.length == 0 and empty_ohlcv.is_empty

    def test_validation_errors(self, sample_timestamps: tuple[Timestamp, ...]) -> None:
        # length mismatch
        with pytest.raises(ValueError, match="All OHLCV data columns must have the same length"):
            OHLCV(
                timestamps=sample_timestamps,  # e.g. 4 stamps
                opens=(Decimal("100"),),  # 1 value
                highs=(Decimal("101"),),
                lows=(Decimal("99"),),
                closes=(Decimal("101"),),
                volumes=(Decimal("1000"),),
                is_closed=(True,),
                symbol="BTCUSDT",
                timeframe="1h",
            )

        # unsorted timestamps
        now = datetime.now(UTC)
        unsorted_ts = (now, now - timedelta(hours=1))
        with pytest.raises(ValueError, match="Timestamps must be sorted"):
            OHLCV(
                timestamps=unsorted_ts,
                opens=(Decimal("100"), Decimal("101")),
                highs=(Decimal("102"), Decimal("103")),
                lows=(Decimal("99"), Decimal("100")),
                closes=(Decimal("101"), Decimal("102")),
                volumes=(Decimal("1000"), Decimal("1100")),
                is_closed=(True, True),
                symbol="BTCUSDT",
                timeframe="1h",
            )

    def test_indexing_and_slicing(self, ohlcv: OHLCV) -> None:
        bar = ohlcv[0]
        assert isinstance(bar, Bar)
        assert bar.ts == ohlcv.timestamps[0]
        assert (bar.open, bar.high, bar.low, bar.close, bar.volume, bar.is_closed) == (
            ohlcv.opens[0],
            ohlcv.highs[0],
            ohlcv.lows[0],
            ohlcv.closes[0],
            ohlcv.volumes[0],
            ohlcv.is_closed[0],
        )

        sliced = ohlcv[1:3]
        assert isinstance(sliced, OHLCV)
        assert len(sliced) == 2
        assert sliced.timestamps == ohlcv.timestamps[1:3]
        assert sliced.opens == ohlcv.opens[1:3]

        with pytest.raises(IndexError):
            _ = ohlcv[999]
        with pytest.raises(TypeError, match="OHLCV indices must be integers or slices"):
            _ = ohlcv["invalid"]  # type: ignore

    def test_iteration(self, ohlcv: OHLCV) -> None:
        bars = list(ohlcv)
        assert len(bars) == len(ohlcv)
        for i, b in enumerate(bars):
            assert isinstance(b, Bar)
            assert b.ts == ohlcv.timestamps[i]
            assert b.open == ohlcv.opens[i]

    def test_slice_by_time(self, ohlcv: OHLCV) -> None:
        start, end = ohlcv.timestamps[1], ohlcv.timestamps[2]
        got = ohlcv.slice_by_time(start, end)
        assert len(got) == 2
        assert got.timestamps[0] >= start and got.timestamps[-1] <= end

        with pytest.raises(ValueError, match="Start time must be <= end time"):
            _ = ohlcv.slice_by_time(end, start)

        future_start = ohlcv.timestamps[-1] + timedelta(hours=1)
        future_end = future_start + timedelta(hours=1)
        empty = ohlcv.slice_by_time(future_start, future_end)
        assert len(empty) == 0


# ---------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------


class TestOHLCVConversion:
    def test_to_series(self, ohlcv: OHLCV) -> None:
        series = ohlcv.to_series()
        for key in ("opens", "highs", "lows", "closes", "volumes"):
            assert key in series
        for s in series.values():
            assert len(s) == len(ohlcv)
            assert s.symbol == ohlcv.symbol and s.timeframe == ohlcv.timeframe

    def test_from_bars(self, sample_bars: list[Bar]) -> None:
        obj = OHLCV.from_bars(sample_bars, symbol="BTCUSDT", timeframe="1h")
        assert len(obj) == 4 and obj.symbol == "BTCUSDT" and obj.timeframe == "1h"

        first = obj[0]
        assert isinstance(first, Bar)
        assert (first.ts, first.open) == (sample_bars[0].ts, sample_bars[0].open)

        with pytest.raises(ValueError, match="Cannot create OHLCV from empty bar list"):
            _ = OHLCV.from_bars([])

        # defaults
        obj_def = OHLCV.from_bars(sample_bars)
        assert obj_def.symbol == "UNKNOWN" and obj_def.timeframe == "1h"


# ---------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------


class TestOHLCVSerialization:
    def test_to_from_dict_roundtrip(self, ohlcv: OHLCV) -> None:
        data = ohlcv.to_dict()
        assert data["symbol"] == "BTCUSDT" and data["timeframe"] == "1h"
        for k in (
            "timestamps",
            "opens",
            "highs",
            "lows",
            "closes",
            "volumes",
            "is_closed",
        ):
            assert len(data[k]) == len(ohlcv)

        restored = OHLCV.from_dict(data)
        assert len(restored) == len(ohlcv)
        assert restored.symbol == "BTCUSDT" and restored.timeframe == "1h"
        assert restored.timestamps == ohlcv.timestamps
        assert restored.opens == ohlcv.opens

    def test_from_dict_defaults_is_closed_true(self, sample_ohlcv_data: dict[str, Any]) -> None:
        data = {
            "timestamps": [iso(ts) for ts in sample_ohlcv_data["timestamps"]],
            "opens": [f(x) for x in sample_ohlcv_data["opens"]],
            "highs": [f(x) for x in sample_ohlcv_data["highs"]],
            "lows": [f(x) for x in sample_ohlcv_data["lows"]],
            "closes": [f(x) for x in sample_ohlcv_data["closes"]],
            "volumes": [f(x) for x in sample_ohlcv_data["volumes"]],
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            # intentionally omit "is_closed"
        }
        obj = OHLCV.from_dict(data)
        assert len(obj) == 4
        assert all(obj.is_closed), "Missing is_closed should default to all True"
