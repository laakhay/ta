"""Tests for Series + align_series."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from laakhay.ta.core.series import Series, align_series
from laakhay.ta.core.types import Price

# ---------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------

UTC = UTC


def ts(*parts) -> tuple[datetime, ...]:
    """Datetime tuple helper: ts((y,m,d,h=0), ...) -> (dt1, dt2, ...)."""
    out = []
    for p in parts:
        if len(p) == 3:
            y, m, d = p
            out.append(datetime(y, m, d, tzinfo=UTC))
        else:
            y, m, d, h = p
            out.append(datetime(y, m, d, h, tzinfo=UTC))
    return tuple(out)


def mk_series(vals, stamps, symbol="BTC", tf="1h"):
    """Create a Series[Price] with Price-wrapped values."""
    return Series[Price](
        timestamps=stamps,
        values=tuple(
            Price(Decimal(str(v))) if not isinstance(v, Price) else v for v in vals
        ),
        symbol=symbol,
        timeframe=tf,
    )


@pytest.fixture
def t0():
    return datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def price_series(t0):
    return mk_series([100], (t0,), symbol="TEST", tf="1s")


@pytest.fixture
def multi_series():
    stamps = ts((2024, 1, 1, 10), (2024, 1, 1, 11))
    return mk_series([100, 200], stamps, symbol="TEST", tf="1s")


@pytest.fixture
def other_series_same_t():
    stamps = ts((2024, 1, 1, 10), (2024, 1, 1, 11))
    return mk_series([50, 75], stamps, symbol="TEST", tf="1s")


# ---------------------------------------------------------------------
# Core creation & basics
# ---------------------------------------------------------------------


def test_creation(price_series, t0):
    s = price_series
    assert len(s) == 1
    assert s.values[0] == Price(Decimal("100"))
    assert s.timestamps[0] == t0


def test_empty_creation():
    s = Series((), (), "TEST", "1s")
    assert len(s) == 0
    assert s.is_empty


def test_validation_length_mismatch(t0):
    with pytest.raises(ValueError, match="same length"):
        Series((t0,), (), "TEST", "1s")


def test_unsorted_timestamps_raises():
    t1, t2 = ts((2024, 1, 1, 12), (2024, 1, 1, 10))
    with pytest.raises(ValueError, match="sorted"):
        mk_series([100, 101], (t1, t2))


def test_indexing_and_iteration(multi_series):
    # index returns (timestamp, value)
    assert multi_series[0] == (multi_series.timestamps[0], multi_series.values[0])
    assert multi_series[1] == (multi_series.timestamps[1], multi_series.values[1])
    pairs = list(multi_series)
    assert pairs == [
        (multi_series.timestamps[0], multi_series.values[0]),
        (multi_series.timestamps[1], multi_series.values[1]),
    ]


def test_index_errors(price_series):
    with pytest.raises(IndexError):
        _ = price_series[1]
    with pytest.raises(TypeError, match="indices"):
        _ = price_series["nope"]  # type: ignore
    with pytest.raises(TypeError):
        _ = price_series[object()]  # type: ignore


def test_properties_nonempty_and_empty():
    s = mk_series([100, 101], ts((2024, 1, 1, 10), (2024, 1, 1, 11)))
    assert s.length == 2 and not s.is_empty
    e = mk_series([], ())
    assert e.length == 0 and e.is_empty


# ---------------------------------------------------------------------
# Arithmetic (element-wise & scalar) + error paths
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "op, expected0, expected1",
    [
        ("+", Decimal("150"), Decimal("275")),  # 100+50, 200+75
        ("-", Decimal("50"), Decimal("125")),  # 100-50, 200-75
        ("*", Decimal("5000"), Decimal("15000")),  # 100*50, 200*75
        ("/", Decimal("2"), Decimal("2.666666666666666666666666667")),
        ("%", Decimal("0"), Decimal("50")),
        ("**", Decimal("1E+100"), Decimal("3.777893186295716170956800000E+172")),
    ],
)
def test_elementwise_ops(multi_series, other_series_same_t, op, expected0, expected1):
    left, right = multi_series, other_series_same_t
    result = eval(f"left {op} right")
    assert len(result) == 2
    assert result.values[0] == Price(expected0)
    assert result.values[1] == Price(expected1)


@pytest.mark.parametrize(
    "op, scalar, expected",
    [
        ("+", 25, Decimal("125")),
        ("-", 25, Decimal("75")),
        ("*", Decimal("2.5"), Decimal("250")),
        ("/", 4, Decimal("25")),
        ("%", 7, Decimal("2")),
        ("**", 3, Decimal("1000000")),
    ],
)
def test_scalar_ops(price_series, op, scalar, expected):
    result = eval(f"price_series {op} scalar")
    assert result.values[0] == Price(expected)


@pytest.mark.parametrize("op", ["/", "%"])
def test_zero_division_scalar(price_series, op):
    with pytest.raises(ValueError):
        _ = eval(f"price_series {op} 0")


@pytest.mark.parametrize("op", ["+", "-", "*", "/", "%", "**"])
def test_type_error_in_ops_with_series_values(t0, op):
    s1 = mk_series([100], (t0,), symbol="TEST", tf="1s")
    s2 = Series((t0,), ("invalid",), "TEST", "1s")
    with pytest.raises(TypeError):
        _ = eval(f"s1 {op} s2")


@pytest.mark.parametrize("rhs", ["invalid", object()])
@pytest.mark.parametrize("op", ["+", "-", "*", "/", "%"])
def test_type_error_in_ops_with_scalar(price_series, op, rhs):
    with pytest.raises(TypeError):
        _ = eval(f"price_series {op} rhs")


def test_cross_instrument_arithmetic_rejected():
    t = ts((2024, 1, 1))
    s1 = mk_series([100.0], t, symbol="BTC", tf="1h")
    s2 = mk_series([200.0], t, symbol="ETH", tf="4h")
    with pytest.raises(ValueError):
        _ = s1 + s2


def test_misaligned_timestamps_rejected():
    s1 = mk_series([100.0, 101.0], ts((2024, 1, 1, 10), (2024, 1, 1, 11)))
    s2 = mk_series([200.0, 201.0], ts((2024, 1, 1, 12), (2024, 1, 1, 13)))
    with pytest.raises(ValueError, match="timestamp alignment"):
        _ = s1 + s2


def test_different_lengths_rejected():
    s1 = mk_series([100.0], ts((2024, 1, 1, 10)))
    s2 = mk_series([200.0, 300.0], ts((2024, 1, 1, 11), (2024, 1, 1, 12)))
    with pytest.raises(ValueError, match="different lengths"):
        _ = s1 + s2


# ---------------------------------------------------------------------
# Unary
# ---------------------------------------------------------------------


def test_unary_neg_pos(price_series, t0):
    neg = -price_series
    assert neg.values[0] == Price(Decimal("-100"))
    pos = +price_series
    assert pos.values[0] == Price(Decimal("100"))


def test_unary_pos_preserves_sign_for_negative(t0):
    s = mk_series([-100], (t0,))
    assert (+s).values[0] == Price(Decimal("-100"))


def test_unary_neg_type_error(t0):
    s = Series((t0,), ("invalid",), "TEST", "1s")
    with pytest.raises(TypeError):
        _ = -s


# ---------------------------------------------------------------------
# Serialization & type aliases
# ---------------------------------------------------------------------


def test_roundtrip_to_from_dict(price_series):
    data = price_series.to_dict()
    assert data["symbol"] == "TEST" and data["timeframe"] == "1s"
    restored = Series.from_dict(data)
    assert restored == price_series


def test_from_dict_parses_types():
    data = {
        "timestamps": ["2024-01-01T10:00:00+00:00"],
        "values": [100.0],
        "symbol": "BTC",
        "timeframe": "1h",
    }
    s = Series[Price].from_dict(data)
    assert s.timestamps[0] == datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    assert s.values[0] == Price(100.0)


def test_type_aliases_exist():
    from laakhay.ta.core.series import PriceSeries, QtySeries

    assert PriceSeries is not None and QtySeries is not None


# ---------------------------------------------------------------------
# slice_by_time
# ---------------------------------------------------------------------


def test_slice_by_time_range():
    stamps = ts((2024, 1, 1, 10), (2024, 1, 1, 11), (2024, 1, 1, 12), (2024, 1, 1, 13))
    s = mk_series([100, 101, 102, 103], stamps)
    start, end = stamps[1], stamps[2]
    r = s.slice_by_time(start, end)
    assert r.timestamps == (stamps[1], stamps[2])
    assert r.values[0] == Price(101) and r.values[1] == Price(102)
    assert r.symbol == s.symbol and r.timeframe == s.timeframe


def test_slice_by_time_invalid_range():
    s = mk_series([100], ts((2024, 1, 1, 10)))
    with pytest.raises(ValueError):
        _ = s.slice_by_time(
            datetime(2024, 1, 1, 12, tzinfo=UTC), datetime(2024, 1, 1, 11, tzinfo=UTC)
        )


def test_slice_by_time_empty_result():
    s = mk_series([100], ts((2024, 1, 1, 10)))
    r = s.slice_by_time(
        datetime(2024, 1, 1, 12, tzinfo=UTC), datetime(2024, 1, 1, 13, tzinfo=UTC)
    )
    assert len(r.timestamps) == 0 and len(r.values) == 0
    assert r.symbol == s.symbol and r.timeframe == s.timeframe


# ---------------------------------------------------------------------
# align_series
# ---------------------------------------------------------------------


def test_align_series_inner(multi_series, other_series_same_t):
    a, b = align_series(multi_series, other_series_same_t, how="inner")
    assert a.timestamps == multi_series.timestamps
    assert b.timestamps == other_series_same_t.timestamps
    assert a.values == multi_series.values
    assert b.values == other_series_same_t.values


def test_align_series_outer_ffill():
    base = datetime(2024, 1, 1, tzinfo=UTC)
    t0, t1, t2 = base, base + timedelta(hours=1), base + timedelta(hours=2)
    left = mk_series([100, 101], (t0, t1))
    right = mk_series([200, 201], (t1, t2))
    al, ar = align_series(
        left,
        right,
        how="outer",
        fill="ffill",
        left_fill_value=left.values[0],
        right_fill_value=right.values[0],
    )
    assert al.timestamps == (t0, t1, t2)
    assert ar.timestamps == (t0, t1, t2)
    assert al.values == (Price(100), Price(101), Price(101))
    assert ar.values == (Price(200), Price(200), Price(201))


def test_align_series_symbol_override():
    ts1 = ts((2024, 1, 1))
    btc = mk_series([100], ts1, symbol="BTC")
    eth = mk_series([200], ts1, symbol="ETH")
    with pytest.raises(ValueError, match="different symbols"):
        align_series(btc, eth)
    a_btc, a_eth = align_series(btc, eth, symbol="BTC-ETH", timeframe="1h")
    assert a_btc.symbol == a_eth.symbol == "BTC-ETH"
    diff = a_btc - a_eth
    assert diff.symbol == "BTC-ETH" and diff.values[0] == Price(Decimal("-100"))


def test_align_series_outer_without_fill_raises():
    base = datetime(2024, 1, 1, tzinfo=UTC)
    left = mk_series([100], (base,))
    right = mk_series([200], (base + timedelta(hours=1),))
    with pytest.raises(ValueError, match="Missing value"):
        align_series(left, right, how="outer")


def test_align_series_unsupported_strategy():
    s1 = mk_series([100], ts((2024, 1, 1, 10)))
    s2 = mk_series([200], ts((2024, 1, 1, 11)))
    with pytest.raises(ValueError, match="Unsupported alignment strategy 'invalid'"):
        align_series(s1, s2, how="invalid")


def test_align_series_diff_symbols_or_timeframes_without_override():
    s1 = mk_series([100], ts((2024, 1, 1, 10)), symbol="BTC", tf="1h")
    s2 = mk_series([200], ts((2024, 1, 1, 11)), symbol="ETH", tf="4h")
    with pytest.raises(ValueError, match="different symbols"):
        align_series(s1, s2, how="inner")
    s3 = mk_series([200], ts((2024, 1, 1, 11)), symbol="BTC", tf="4h")
    with pytest.raises(ValueError, match="different timeframes"):
        align_series(s1, s3, how="inner")


def test_align_series_empty_inner_result_raises():
    s1 = mk_series([100], ts((2024, 1, 1, 10)))
    s2 = mk_series([200], ts((2024, 1, 1, 11)))
    with pytest.raises(ValueError, match="empty timestamp set"):
        align_series(s1, s2, how="inner")
