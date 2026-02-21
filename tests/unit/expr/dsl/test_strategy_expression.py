from datetime import timezone, datetime, timedelta
UTC = timezone.utc

import pytest

from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr.dsl import (
    StrategyError,
    compile_expression,
    compute_trim,
    extract_indicator_nodes,
    parse_expression_text,
)


def dataset():
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i) for i in range(50)]
    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h"))
    return ds


def test_parse_expression_text():
    expr = parse_expression_text("(sma(20) > sma(50)) and (rsi(14) < 30)")
    indicators = extract_indicator_nodes(expr)
    names = [node.name for node in indicators]
    assert names == ["sma", "sma", "rsi"]
    assert compute_trim(indicators) >= 50


def test_compile_expression_runs_against_dataset():
    expr = compile_expression("(sma(5) > sma(8))")
    result = expr.run(dataset())
    assert isinstance(result, dict)
    series = result[("BTCUSDT", "1h", "default")]
    # SMA(5) produces 46 values, SMA(8) produces 43 values from 50 bars
    # After alignment (intersection), we get 43 values
    assert len(series) == 43


def test_parse_invalid_expression():
    with pytest.raises(StrategyError):
        parse_expression_text("unknownFunc(5)")


def test_parse_sma_positional_period():
    expr = parse_expression_text("sma(20)")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].args[0].value == 20


def test_parse_in_channel_expression():
    expr = parse_expression_text("in_channel(close, bb_upper(20, 2), bb_lower(20, 2))")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].name == "in_channel"
