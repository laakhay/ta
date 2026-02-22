from datetime import UTC, datetime, timedelta

import pytest

from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr.dsl import (
    StrategyError,
    compile_expression,
    extract_indicator_nodes,
    parse_expression_text,
)

UTC = UTC


def dataset():
    """Create a test dataset with OHLCV data."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i) for i in range(50)]
    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h"))
    return ds


def test_parse_indicator_with_explicit_source():
    """Test parsing indicator with explicit source expression."""
    expr = parse_expression_text("sma(BTC.price, period=20)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert indicators[0].name == "sma"
    assert indicators[0].kwargs.get("period").value == 20
    assert len(indicators[0].args) == 1
    assert indicators[0].args[0].field == "close"


def test_parse_indicator_with_explicit_source_trades():
    """Test parsing indicator with explicit trades source."""
    expr = parse_expression_text("sma(BTC.trades.volume, period=20)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert indicators[0].name == "sma"
    assert len(indicators[0].args) == 1
    from laakhay.ta.expr.ir.nodes import SourceRefNode

    assert isinstance(indicators[0].args[0], SourceRefNode)
    assert indicators[0].args[0].source == "trades"
    assert indicators[0].args[0].field == "volume"


def test_parse_indicator_with_explicit_source_orderbook():
    """Test parsing indicator with explicit orderbook source."""
    expr = parse_expression_text("sma(binance.BTC.orderbook.imbalance, period=20)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert indicators[0].name == "sma"
    assert len(indicators[0].args) == 1
    from laakhay.ta.expr.ir.nodes import SourceRefNode

    assert isinstance(indicators[0].args[0], SourceRefNode)
    assert indicators[0].args[0].exchange == "binance"
    assert indicators[0].args[0].source == "orderbook"
    assert indicators[0].args[0].field == "imbalance"


def test_parse_indicator_with_literal_first_arg():
    """Test that literal first argument still works (backward compatibility)."""
    expr = parse_expression_text("sma(20)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert indicators[0].name == "sma"
    assert len(indicators[0].args) == 1
    # When first arg is literal, it goes to args
    assert indicators[0].args[0].value == 20


def test_parse_indicator_with_keyword_period():
    """Test that keyword period still works."""
    expr = parse_expression_text("sma(period=20)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert indicators[0].name == "sma"
    assert indicators[0].kwargs.get("period").value == 20
    assert len(indicators[0].args) == 0


def test_parse_indicator_expr_and_keyword_conflict():
    """Test that specifying a param both as positional and keyword raises error."""
    # This should work - period as keyword is fine when input_expr is positional
    expr = parse_expression_text("sma(BTC.price, period=20)")
    assert expr is not None
    # This should fail - period specified twice
    with pytest.raises(StrategyError, match="cannot be specified both"):
        parse_expression_text("sma(20, period=20)")


def test_compile_indicator_with_explicit_source():
    """Test compiling and running indicator with explicit source."""
    from decimal import Decimal

    expr = compile_expression("sma(BTC.price, period=5)")
    result = expr.run(dataset())
    assert isinstance(result, dict)
    series = result[("BTCUSDT", "1h", "default")]
    # Should produce valid SMA values (may be Decimal/Price type)
    assert len(series) > 0
    assert all(isinstance(v, int | float | Decimal) for v in series.values)


def test_compile_indicator_with_nested_expression():
    """Test indicator with nested expression as input."""
    # Test with a simple binary operation
    expr = compile_expression("sma(BTC.high + BTC.low, period=5)")
    result = expr.run(dataset())
    assert isinstance(result, dict)
    series = result[("BTCUSDT", "1h", "default")]
    assert len(series) > 0


def test_serialize_indicator_with_input_expr():
    """Test serialization of CallNode with explicit input in args[0]."""
    from laakhay.ta.expr.ir.serialize import ir_from_dict, ir_to_dict

    expr = parse_expression_text("sma(BTC.price, period=20)")
    indicators = extract_indicator_nodes(expr)
    indicator = indicators[0]

    # Serialize
    serialized = ir_to_dict(indicator)
    assert "args" in serialized
    assert serialized["args"][0]["type"] == "source_ref"

    # Deserialize
    deserialized = ir_from_dict(serialized)
    assert deserialized.name == "sma"
    assert deserialized.kwargs.get("period").value == 20
    assert len(deserialized.args) == 1
    from laakhay.ta.expr.ir.nodes import SourceRefNode

    assert isinstance(deserialized.args[0], SourceRefNode)


def test_multiple_indicators_with_explicit_sources():
    """Test multiple indicators with different explicit sources."""
    expr = parse_expression_text("sma(BTC.price, period=20) > sma(BTC.volume, period=10)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 2
    # Both should have args
    assert len(indicators[0].args) == 1
    assert len(indicators[1].args) == 1
    assert indicators[0].args[0].field == "close"
    assert indicators[1].args[0].field == "volume"


def test_indicator_with_timeframe_in_source():
    """Test indicator with explicit source that includes timeframe."""
    # Note: Python syntax doesn't allow BTC.1h.price (1h is not a valid identifier)
    # This would need bracket notation like BTC["1h"].price, which isn't supported yet
    # For now, test that the basic functionality works
    expr = parse_expression_text("sma(BTC.price, period=20)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert len(indicators[0].args) == 1
    # Timeframe support would require additional parser changes for bracket notation


def test_compile_expression_with_fib_level_down_indicator():
    expr = compile_expression("close < fib_level_down(level=0.618, left=2, right=2)")
    result = expr.run(dataset())
    assert isinstance(result, dict)
    series = result[("BTCUSDT", "1h", "default")]
    assert len(series) > 0


def test_compile_expression_with_fib_alias_indicator():
    expr = compile_expression("close < fib_down(level=0.5, left=2, right=2)")
    result = expr.run(dataset())
    assert isinstance(result, dict)
    series = result[("BTCUSDT", "1h", "default")]
    assert len(series) > 0


def test_compile_expression_with_swing_index_indicator():
    expr = compile_expression("close > swing_high_at(index=1, left=2, right=2)")
    result = expr.run(dataset())
    assert isinstance(result, dict)
    series = result[("BTCUSDT", "1h", "default")]
    assert len(series) > 0


def test_compile_expression_with_fib_leg_and_pairing_mode():
    expr = compile_expression(
        "close < fib_level_down(level=0.618, left=2, right=2, leg=1, pairing_mode='latest_valid')"
    )
    result = expr.run(dataset())
    assert isinstance(result, dict)
    series = result[("BTCUSDT", "1h", "default")]
    assert len(series) > 0
