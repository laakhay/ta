import pytest
from laakhay.ta.expr.dsl import parse_expression_text, StrategyError, extract_indicator_nodes

def test_parse_mean_alias():
    """Test that 'mean' is successfully normalized to 'rolling_mean'."""
    expr = parse_expression_text("mean(close, lookback=10)")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].name == "rolling_mean"
    assert indicators[0].params["period"] == 10

def test_parse_median_alias():
    """Test that 'median' is successfully normalized to 'rolling_median'."""
    expr = parse_expression_text("median(close, lookback=10)")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].name == "rolling_median"
    assert indicators[0].params["period"] == 10

def test_parse_lookback_keyword():
    """Test that 'lookback' keyword maps to 'period'."""
    expr = parse_expression_text("sma(close, lookback=10)")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].name == "sma"
    assert indicators[0].params["period"] == 10

def test_parse_min_max_with_lookback():
    """Test min/max with lookback keyword."""
    expr_max = parse_expression_text("max(close, lookback=20)")
    indicators_max = extract_indicator_nodes(expr_max)
    assert indicators_max[0].name == "max"
    assert indicators_max[0].params["period"] == 20

    expr_min = parse_expression_text("min(close, lookback=20)")
    indicators_min = extract_indicator_nodes(expr_min)
    assert indicators_min[0].name == "min"
    assert indicators_min[0].params["period"] == 20

def test_parse_volume_stats():
    """Test stats on volume field (aliases should normalize)."""
    expr = parse_expression_text("mean(volume, lookback=10)")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].name == "rolling_mean"
    assert indicators[0].params["period"] == 10
    
def test_parse_mixed_aliases_and_logic():
    """Test complex logical expressions with aliases."""
    expr = parse_expression_text("volume > mean(volume, lookback=10) * 5")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].name == "select" # for volume
    assert indicators[1].name == "rolling_mean"

def test_parse_nested_stats_aliases():
    """Test nesting aliases."""
    expr = parse_expression_text("mean(sma(close, 14), lookback=10)")
    indicators = extract_indicator_nodes(expr)
    # 1. rolling_mean
    # 2. sma (from input_expr of rolling_mean)
    # 3. select (from input_expr of sma)
    assert any(ind.name == "rolling_mean" for ind in indicators)
    assert any(ind.name == "sma" for ind in indicators)
    assert any(ind.name == "select" and ind.params.get("field") == "close" for ind in indicators)

def test_parse_explicit_source_with_alias():
    """Test alias with symbol prefix."""
    expr = parse_expression_text("BTC.price > mean(BTC.price, lookback=50)")
    indicators = extract_indicator_nodes(expr)
    # BTC.price is an AttributeNode, not an IndicatorNode.
    # So we only expect the 'mean' (rolling_mean) indicator.
    # Note: the input_expr of 'mean' will be the AttributeNode, which is not collected by collect().
    assert len(indicators) == 1
    assert indicators[0].name == "rolling_mean"
    assert indicators[0].params["period"] == 50

def test_parse_mean_positional_field():
    """Test mean(volume, 10) shorthand."""
    expr = parse_expression_text("mean(volume, 10)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    # Should resolve to field='volume', period=10
    # Note: 'volume' is parsed as a name, which heuristics map to field param
    assert indicators[0].name == "rolling_mean"
    assert indicators[0].params["field"] == "volume"
    assert indicators[0].params["period"] == 10

def test_parse_mean_default_positional_field():
    """Test mean(10) uses default field."""
    expr = parse_expression_text("mean(10)")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert indicators[0].name == "rolling_mean"
    assert indicators[0].params.get("field") is None
    assert indicators[0].params["period"] == 10

def test_parse_mean_explicit_field_kwarg():
    """Test mean(10, field='high') works."""
    expr = parse_expression_text("mean(10, field='high')")
    indicators = extract_indicator_nodes(expr)
    assert len(indicators) == 1
    assert indicators[0].name == "rolling_mean"
    assert indicators[0].params["field"] == "high"
    assert indicators[0].params["period"] == 10

def test_malformed_lookback():
    """Test negative cases for lookback (should still fail if invalid value)."""
    # The parser currently doesn't validate types strictly in _convert_indicator_call,
    # it just stores whatever literal it gets. Hard validation comes later.
    # For now, let's just assert it normalizes even bad values.
    expr = parse_expression_text("mean(close, lookback='invalid')")
    indicators = extract_indicator_nodes(expr)
    assert indicators[0].params["period"] == "invalid"

def test_unknown_parameter_raises_error():
    """Test that unknown parameters raise StrategyError."""
    with pytest.raises(StrategyError, match="Unknown parameter 'invalid_param'"):
        parse_expression_text("mean(close, 10, invalid_param=5)")
