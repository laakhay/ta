"""Ttests for laakhay.ta.core.bar.Bar."""

from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any

from laakhay.ta.core.bar import Bar

UTC = timezone.utc


# ---------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------

class TestBar:
    def test_creation_and_validation(self, sample_datetime_utc: datetime) -> None:
        # happy path (coercion via from_raw)
        bar = Bar.from_raw(
            ts=sample_datetime_utc, open=100, high=110, low=95, close=105, volume=1000, is_closed=True
        )
        assert bar.ts == sample_datetime_utc
        assert bar.open == Decimal("100")
        assert bar.is_closed is True

        # high < low
        with pytest.raises(ValueError, match="High must be >= low"):
            Bar.from_raw(sample_datetime_utc, 100, 90, 95, 105, 1000, True)

        # high < open/close
        with pytest.raises(ValueError, match="High must be >= open and close"):
            Bar.from_raw(sample_datetime_utc, 100, 95, 90, 105, 1000, True)

        # low > open/close
        with pytest.raises(ValueError, match="Low must be <= open and close"):
            Bar.from_raw(sample_datetime_utc, 100, 110, 105, 95, 1000, True)

        # negative volume
        with pytest.raises(ValueError, match="Volume must be >= 0"):
            Bar.from_raw(sample_datetime_utc, 100, 110, 95, 105, -1, True)

    def test_properties(self, sample_datetime_utc: datetime) -> None:
        bar = Bar.from_raw(sample_datetime_utc, 100, 110, 90, 105, 1000, True)
        assert bar.hlc3 == Decimal("101.6666666666666666666666667")  # (110+90+105)/3
        assert bar.ohlc4 == Decimal("101.25")                         # (100+110+90+105)/4
        assert bar.hl2 == Decimal("100")                              # (110+90)/2
        assert bar.body_size == Decimal("5")                          # |105-100|
        assert bar.upper_wick == Decimal("5")                         # 110-max(100,105)
        assert bar.lower_wick == Decimal("10")                        # min(100,105)-90
        assert bar.total_range == Decimal("20")                       # 110-90

    @pytest.mark.parametrize(
        "o,h,l,c,v,closed,exp_o,exp_v,exp_closed",
        [
            (100,   110, 95, 105, 1000, True,  "100",   "1000",   True),
            ("100.5","110.5","95.5","105.5","1000.5", True, "100.5","1000.5", True),
            (100.5, 110.5, 95.5, 105.5, 1000.5, False, "100.5","1000.5", False),
        ],
    )
    def test_from_raw_coercion(
        self, sample_datetime_utc: datetime, o, h, l, c, v, closed, exp_o, exp_v, exp_closed
    ) -> None:
        bar = Bar.from_raw(sample_datetime_utc, o, h, l, c, v, closed)
        assert bar.open == Decimal(exp_o)
        assert bar.volume == Decimal(exp_v)
        assert bar.is_closed is exp_closed

    def test_from_dict_key_variants(
        self,
        sample_bar_dict: Dict[str, Any],
        sample_bar_dict_alternative_keys: Dict[str, Any],
        sample_bar_dict_short_keys: Dict[str, Any],
    ) -> None:
        assert Bar.from_dict(sample_bar_dict).open == Decimal("100")
        assert Bar.from_dict(sample_bar_dict_alternative_keys).open == Decimal("100")
        assert Bar.from_dict(sample_bar_dict_short_keys).open == Decimal("100")

    def test_repr(self, sample_datetime_utc: datetime) -> None:
        bar = Bar.from_raw(sample_datetime_utc, 100, 110, 95, 105, 1000, True)
        s = repr(bar)
        for token in ("Bar(", "o=100", "h=110", "l=95", "c=105", "vol=1000", "closed=True"):
            assert token in s

    def test_edge_cases(self, sample_datetime_utc: datetime) -> None:
        # doji
        doji = Bar.from_raw(sample_datetime_utc, 100, 105, 95, 100, 1000, True)
        assert doji.body_size == Decimal("0")

        # zero volume
        zv = Bar.from_raw(sample_datetime_utc, 100, 100, 100, 100, 0, True)
        assert zv.volume == Decimal("0")

        # hammer
        hammer = Bar.from_raw(sample_datetime_utc, 100, 102, 90, 101, 1000, True)
        assert hammer.lower_wick == Decimal("10")
        assert hammer.upper_wick == Decimal("1")


# ---------------------------------------------------------------------
# Critical From-Dict behaviors (audit)
# ---------------------------------------------------------------------

class TestBarFromDictCriticalIssues:
    def test_preserves_falsy_values(self) -> None:
        data = {
            "ts": "2024-01-01T00:00:00Z",
            "open": 0.0,
            "high": 1.0,
            "low": 0.0,
            "close": 0.0,
            "volume": 0.0,    # zero
            "is_closed": False,  # false
        }
        bar = Bar.from_dict(data)
        assert bar.open == Decimal("0.0")
        assert bar.close == Decimal("0.0")
        assert bar.volume == Decimal("0.0")
        assert bar.is_closed is False

    def test_preserves_midnight_timestamp(self) -> None:
        data = {
            "ts": "2024-01-01T00:00:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000.0,
            "is_closed": True,
        }
        bar = Bar.from_dict(data)
        assert bar.ts == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_missing_required_field_raises(self) -> None:
        data = {
            "ts": "2024-01-01T00:00:00Z",
            "open": 100.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000.0,
        }
        with pytest.raises(ValueError, match="Missing required field 'high'"):
            Bar.from_dict(data)

    def test_none_value_raises(self) -> None:
        data = {
            "ts": "2024-01-01T00:00:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": None,
            "close": 100.5,
            "volume": 1000.0,
        }
        with pytest.raises(ValueError, match=r"Field 'low' \(alias 'low'\) cannot be None"):
            Bar.from_dict(data)

    @pytest.mark.parametrize(
        "val,expected",
        [("false", False), ("true", True), ("False", False), ("True", True)],
    )
    def test_is_closed_string_parsed(self, val, expected) -> None:
        data = {
            "ts": "2024-01-01T00:00:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000.0,
            "is_closed": val,
        }
        assert Bar.from_dict(data).is_closed is expected

    def test_is_closed_invalid_string_raises(self) -> None:
        data = {
            "ts": "2024-01-01T00:00:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000.0,
            "is_closed": "maybe",
        }
        with pytest.raises(ValueError, match="Unrecognised boolean value"):
            Bar.from_dict(data)
