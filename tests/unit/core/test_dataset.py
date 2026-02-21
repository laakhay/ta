"""Tests for Dataset, DatasetKey, DatasetMetadata, and helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from laakhay.ta.core import OHLCV, Dataset, DatasetKey, DatasetMetadata, Series
from laakhay.ta.core.dataset import dataset as make_dataset
from laakhay.ta.core.types import Price

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def mk_series_from_fixture(sample_series_data: dict[str, Any], symbol="BTCUSDT", tf="1h"):
    return Series[Price](
        timestamps=sample_series_data["timestamps"],
        values=sample_series_data["values"],
        symbol=symbol,
        timeframe=tf,
    )


def mk_ohlcv_from_fixture(sample_ohlcv_data: dict[str, Any], symbol="BTCUSDT", tf="1h"):
    return OHLCV(
        timestamps=sample_ohlcv_data["timestamps"],
        opens=sample_ohlcv_data["opens"],
        highs=sample_ohlcv_data["highs"],
        lows=sample_ohlcv_data["lows"],
        closes=sample_ohlcv_data["closes"],
        volumes=sample_ohlcv_data["volumes"],
        is_closed=sample_ohlcv_data["is_closed"],
        symbol=symbol,
        timeframe=tf,
    )


# ---------------------------------------------------------------------
# DatasetKey
# ---------------------------------------------------------------------


class TestDatasetKey:
    def test_creation_and_defaults(self):
        k = DatasetKey(symbol="BTCUSDT", timeframe="1h", source="binance")
        assert (k.symbol, k.timeframe, k.source) == ("BTCUSDT", "1h", "binance")

        k2 = DatasetKey(symbol="BTCUSDT", timeframe="1h")
        assert k2.source == "default"

    def test_str_and_roundtrip_dict(self):
        k = DatasetKey(symbol="BTCUSDT", timeframe="1h", source="binance")
        assert str(k) == "BTCUSDT|1h|binance"
        d = k.to_dict()
        assert d == {"symbol": "BTCUSDT", "timeframe": "1h", "source": "binance"}
        k2 = DatasetKey.from_dict(d)
        assert k2 == k

    def test_from_dict_default_source(self):
        k = DatasetKey.from_dict({"symbol": "BTCUSDT", "timeframe": "1h"})
        assert k.source == "default"

    def test_immutable(self):
        k = DatasetKey("BTCUSDT", "1h")
        with pytest.raises(AttributeError):
            k.symbol = "ETHUSDT"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------
# DatasetMetadata
# ---------------------------------------------------------------------


class TestDatasetMetadata:
    def test_creation_and_defaults(self):
        md = DatasetMetadata(description="Test dataset", tags={"crypto", "test"})
        assert md.description == "Test dataset"
        assert md.tags == {"crypto", "test"}
        assert isinstance(md.created_at, datetime)

        md2 = DatasetMetadata()
        assert md2.description == ""
        assert md2.tags == set()
        assert isinstance(md2.created_at, datetime)

    def test_roundtrip_dict(self):
        d = {
            "description": "Test dataset",
            "tags": ["crypto", "test"],
            "created_at": "2024-01-01T00:00:00Z",
        }
        md = DatasetMetadata.from_dict(d)
        assert md.description == "Test dataset"
        assert md.tags == {"crypto", "test"}
        assert isinstance(md.created_at, datetime)
        out = md.to_dict()
        assert out["description"] == "Test dataset"
        assert set(out["tags"]) == {"crypto", "test"}
        assert "created_at" in out


# ---------------------------------------------------------------------
# Dataset core
# ---------------------------------------------------------------------


class TestDatasetCore:
    def test_empty_and_metadata(self):
        ds = Dataset()
        assert len(ds) == 0 and ds.symbols == set() and ds.timeframes == set() and ds.sources == set()

        md = DatasetMetadata(description="X")
        ds2 = Dataset(metadata=md)
        assert ds2.metadata.description == "X"

    def test_add_series_and_sets(self, sample_series_data):
        ds = Dataset()
        s = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s)
        assert len(ds) == 1
        assert ds.symbols == {"BTCUSDT"}
        assert ds.timeframes == {"1h"}
        assert ds.sources == {"default"}

    def test_add_series_with_source(self, sample_series_data):
        ds = Dataset()
        s = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s, source="binance")
        assert len(ds) == 1
        assert ds.sources == {"binance"}

    def test_series_retrieval_found_and_not_found(self, sample_series_data):
        ds = Dataset()
        s = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s)
        assert ds.series("BTCUSDT", "1h") is not None
        assert ds.series("NONEXISTENT", "1h") is None

    def test_properties_multiple(self, sample_series_data):
        ds = Dataset()
        s1 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        s2 = mk_series_from_fixture(sample_series_data, "ETHUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s1)
        ds.add_series("ETHUSDT", "1h", s2)
        assert len(ds) == 2
        assert ds.symbols == {"BTCUSDT", "ETHUSDT"}
        assert ds.timeframes == {"1h"}
        assert ds.sources == {"default"}

    def test_iteration_contains_getitem(self, sample_series_data):
        ds = Dataset()
        s = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s)

        items = list(ds)
        assert len(items) == 1
        key, val = items[0]
        assert key == DatasetKey("BTCUSDT", "1h")

        assert DatasetKey("BTCUSDT", "1h") in ds
        assert DatasetKey("ETHUSDT", "1h") not in ds

        assert len(ds[DatasetKey("BTCUSDT", "1h")]) == len(s)
        with pytest.raises(KeyError):
            _ = ds[DatasetKey("NOPE", "1h")]


# ---------------------------------------------------------------------
# DatasetView
# ---------------------------------------------------------------------


class TestDatasetView:
    def test_view_creation_and_symbol_filter(self, sample_series_data):
        ds = Dataset()
        btc = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        eth = mk_series_from_fixture(sample_series_data, "ETHUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", btc)
        ds.add_series("ETHUSDT", "1h", eth)

        v = ds.select(symbol="BTCUSDT")
        assert len(v) == 1 and v.symbols == {"BTCUSDT"}

        items = list(v)
        assert len(items) == 1 and items[0][0].symbol == "BTCUSDT"

    def test_timeframe_filter(self, sample_series_data):
        ds = Dataset()
        s1 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        s2 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "5m")
        ds.add_series("BTCUSDT", "1h", s1)
        ds.add_series("BTCUSDT", "5m", s2)

        v = ds.select(timeframe="1h")
        assert len(v) == 1 and v.timeframes == {"1h"}

    def test_source_filter(self, sample_series_data):
        ds = Dataset()
        s1 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        s2 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s1, source="binance")
        ds.add_series("BTCUSDT", "1h", s2, source="coinbase")

        v = ds.select(source="binance")
        assert len(v) == 1 and v.sources == {"binance"}

    def test_multiple_filters(self, sample_series_data):
        ds = Dataset()
        s1 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        s2 = mk_series_from_fixture(sample_series_data, "ETHUSDT", "1h")
        s3 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "5m")
        ds.add_series("BTCUSDT", "1h", s1)
        ds.add_series("ETHUSDT", "1h", s2)
        ds.add_series("BTCUSDT", "5m", s3)

        v = ds.select(symbol="BTCUSDT", timeframe="1h")
        assert len(v) == 1
        assert v.symbols == {"BTCUSDT"} and v.timeframes == {"1h"}


# ---------------------------------------------------------------------
# dataset(...) convenience
# ---------------------------------------------------------------------


class TestDatasetConvenience:
    def test_positional(self, sample_series_data):
        s1 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        s2 = mk_series_from_fixture(sample_series_data, "ETHUSDT", "1h")
        ds = make_dataset(s1, s2)
        assert len(ds) == 2 and {"BTCUSDT", "ETHUSDT"} <= ds.symbols

    def test_with_metadata(self, sample_series_data):
        s = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        md = DatasetMetadata(description="Test dataset")
        ds = make_dataset(s, metadata=md)
        assert ds.metadata.description == "Test dataset"

    def test_keyword_args(self, sample_series_data):
        s1 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        s2 = mk_series_from_fixture(sample_series_data, "ETHUSDT", "1h")
        ds = make_dataset(**{"BTCUSDT|1h": s1, "ETHUSDT|1h": s2})
        assert len(ds) == 2 and {"BTCUSDT", "ETHUSDT"} <= ds.symbols

    def test_keyword_with_source(self, sample_series_data):
        s = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds = make_dataset(**{"BTCUSDT|1h|binance": s})
        assert len(ds) == 1 and "binance" in ds.sources


# ---------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------


class TestDatasetSerialization:
    def test_to_dict_and_from_dict(self, sample_series_data):
        ds = Dataset()
        s = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s)
        d = ds.to_dict()
        assert "metadata" in d and "series" in d and len(d["series"]) == 1
        ds2 = Dataset.from_dict(d)
        assert len(ds2) == 1 and "BTCUSDT" in ds2.symbols

    def test_ohlcv_roundtrip(self, sample_ohlcv_data):
        ds = Dataset()
        o = mk_ohlcv_from_fixture(sample_ohlcv_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", o)
        d = ds.to_dict()
        ds2 = Dataset.from_dict(d)
        assert len(ds2) == 1
        got = ds2.series("BTCUSDT", "1h")
        assert isinstance(got, OHLCV)


# ---------------------------------------------------------------------
# Integration & edge behavior
# ---------------------------------------------------------------------


class TestDatasetIntegration:
    def test_multi_symbol_timeframe(self, sample_series_data):
        ds = Dataset()
        btc_1h = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        btc_5m = mk_series_from_fixture(sample_series_data, "BTCUSDT", "5m")
        eth_1h = mk_series_from_fixture(sample_series_data, "ETHUSDT", "1h")

        ds.add_series("BTCUSDT", "1h", btc_1h)
        ds.add_series("BTCUSDT", "5m", btc_5m)
        ds.add_series("ETHUSDT", "1h", eth_1h)

        assert len(ds) == 3
        assert ds.symbols == {"BTCUSDT", "ETHUSDT"}
        assert ds.timeframes == {"1h", "5m"}

        assert len(ds.select(symbol="BTCUSDT")) == 2
        assert len(ds.select(timeframe="1h")) == 2

    def test_different_sources(self, sample_series_data):
        ds = Dataset()
        s1 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        s2 = mk_series_from_fixture(sample_series_data, "BTCUSDT", "1h")
        ds.add_series("BTCUSDT", "1h", s1, source="binance")
        ds.add_series("BTCUSDT", "1h", s2, source="coinbase")

        assert len(ds) == 2 and ds.sources == {"binance", "coinbase"}
        b = ds.series("BTCUSDT", "1h", source="binance")
        c = ds.series("BTCUSDT", "1h", source="coinbase")
        assert b is not None and c is not None and b is not c


# ---------------------------------------------------------------------
# Critical serialization edge cases from audit
# ---------------------------------------------------------------------


class TestDatasetSerializationCriticalIssues:
    def test_symbol_with_underscores_roundtrips(self):
        key = DatasetKey(symbol="BTC_PERP", timeframe="1h", source="binance")
        ds = Dataset()
        s = Series[Price](
            timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
            values=(Price(100.0),),
            symbol="BTC_PERP",
            timeframe="1h",
        )
        ds.add_series(key.symbol, key.timeframe, s, key.source)

        d = ds.to_dict()
        ds2 = Dataset.from_dict(d)

        # Ensure symbol preserved and retrievable
        found = None
        for (
            k,
            v,
        ) in ds2._series.items():  # using internal mapping intentionally for strict check
            if k.symbol == "BTC_PERP":
                found = v
                break
        assert found is not None and found.symbol == "BTC_PERP"

    def test_from_dict_invalid_key_format_is_ignored(self):
        data = {
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "description": "",
                "tags": [],
            },
            "series": {
                "invalid_key": {  # no separators
                    "timestamps": ["2024-01-01T00:00:00+00:00"],
                    "values": [100.0],
                    "symbol": "BTC",
                    "timeframe": "1h",
                }
            },
        }
        ds = Dataset.from_dict(data)
        assert len(ds) == 0

    def test_from_dict_short_key_format_is_ignored(self):
        data = {
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "description": "",
                "tags": [],
            },
            "series": {
                "BTC": {  # only symbol
                    "timestamps": ["2024-01-01T00:00:00+00:00"],
                    "values": [100.0],
                    "symbol": "BTC",
                    "timeframe": "1h",
                }
            },
        }
        ds = Dataset.from_dict(data)
        assert len(ds) == 0
