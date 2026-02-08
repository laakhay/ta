import pytest
from laakhay.ta.expr.dsl import parse_expression_text, StrategyError, extract_indicator_nodes

def test_parse_mean_alias():
    """Test that 'mean' is recognized as an alias (should fail currently)."""
    # This should fail with StrategyError because 'mean' is not yet registered
    # Fixed regex to match actual error message: "Indicator 'mean' not found"
    with pytest.raises(StrategyError, match="Indicator 'mean' not found"):
        parse_expression_text("mean(close, lookback=10)")

def test_parse_median_alias():
    """Test that 'median' is recognized as an alias (should fail currently)."""
    with pytest.raises(StrategyError, match="Indicator 'median' not found"):
        parse_expression_text("median(close, lookback=10)")

def test_parse_lookback_keyword():
    """Test that 'lookback' keyword is recognized (should fail currently or be ignored)."""
    expr = parse_expression_text("sma(close, lookback=10)")
    indicators = extract_indicator_nodes(expr)
    # It shouldn't have 'period' set from 'lookback' yet
    assert indicators[0].params.get("period") != 10
    assert "lookback" in indicators[0].params

def test_parse_min_max_with_lookback():
    """Test min/max with lookback keyword (should fail to map to period)."""
    expr_max = parse_expression_text("max(close, lookback=20)")
    indicators_max = extract_indicator_nodes(expr_max)
    assert indicators_max[0].params.get("period") != 20

    expr_min = parse_expression_text("min(close, lookback=20)")
    indicators_min = extract_indicator_nodes(expr_min)
    assert indicators_min[0].params.get("period") != 20

def test_parse_volume_stats():
    """Test stats on volume field (should fail currently)."""
    with pytest.raises(StrategyError, match="Indicator 'mean' not found"):
        parse_expression_text("mean(volume, lookback=10)")
    
    with pytest.raises(StrategyError, match="Indicator 'median' not found"):
        parse_expression_text("median(volume, lookback=10)")

def test_parse_mixed_aliases_and_logic():
    """Test complex logical expressions with aliases."""
    with pytest.raises(StrategyError, match="Indicator 'mean' not found"):
        parse_expression_text("volume > mean(volume, lookback=10) * 5")

    with pytest.raises(StrategyError, match="Indicator 'mean' not found"):
        parse_expression_text("mean(close, lookback=10) > median(close, lookback=20)")

def test_parse_nested_stats_aliases():
    """Test nesting aliases (if supported by plan later)."""
    with pytest.raises(StrategyError, match="Indicator 'mean' not found"):
        parse_expression_text("mean(sma(14), lookback=10)")

def test_parse_explicit_source_with_alias():
    """Test alias with symbol prefix."""
    with pytest.raises(StrategyError, match="Indicator 'mean' not found"):
        parse_expression_text("BTC.price > mean(BTC.price, lookback=50)")

def test_malformed_lookback():
    """Test negative cases for lookback."""
    with pytest.raises(StrategyError):
        parse_expression_text("mean(close, lookback='invalid')")
