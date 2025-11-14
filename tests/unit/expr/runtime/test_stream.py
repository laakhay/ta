"""Tests for the streaming helper."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from laakhay.ta import ta
from laakhay.ta.core.bar import Bar
from laakhay.ta.expr.runtime.stream import Stream


def _bar(ts: datetime, price: float) -> Bar:
    value = float(price)
    return Bar.from_raw(
        ts=ts,
        open=value,
        high=value,
        low=value,
        close=value,
        volume=1.0,
        is_closed=True,
    )


def test_stream_sma_transition():
    stream = Stream()
    sma = ta.indicator("sma", period=2)
    stream.register("sma2", sma._to_expression())

    base = datetime(2024, 1, 1, tzinfo=UTC)

    stream.update_ohlcv("BTCUSDT", "1h", _bar(base, 100))
    update = stream.update_ohlcv("BTCUSDT", "1h", _bar(base + timedelta(hours=1), 110))

    assert len(update.transitions) == 1
    transition = update.transitions[0]
    assert transition.expression == "sma2"
    assert transition.value == Decimal("105")  # average of 100 and 110


def test_stream_transition_callback_invoked():
    stream = Stream()
    sma = ta.indicator("sma", period=2)
    expr = sma._to_expression()
    events: list[float] = []

    def callback(evt):
        events.append(evt.value)

    stream.register("sma2", expr, on_transition=callback)

    base = datetime(2024, 1, 1, tzinfo=UTC)
    stream.update_ohlcv("BTCUSDT", "1h", _bar(base, 100))
    stream.update_ohlcv("BTCUSDT", "1h", _bar(base + timedelta(hours=1), 110))

    assert events == [Decimal("105")]
