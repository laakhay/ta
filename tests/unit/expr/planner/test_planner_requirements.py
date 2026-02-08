from laakhay.ta.expr.dsl import parse_expression_text
from laakhay.ta.expr.planner import plan_expression

def test_planner_volume_mean_requirements():
    """Test that mean(volume) only requires volume."""
    expr = parse_expression_text("mean(volume, 10)")
    plan = plan_expression(expr)
    
    # Check that 'volume' is required
    assert any(req.name == "volume" for req in plan.requirements.fields)
    
    # Check that 'close' is NOT required (implicit close removed)
    assert not any(req.name == "close" for req in plan.requirements.fields)

def test_planner_close_mean_requirements():
    """Test that mean(close) requires close."""
    expr = parse_expression_text("mean(close, 10)")
    plan = plan_expression(expr)
    
    assert any(req.name == "close" for req in plan.requirements.fields)
