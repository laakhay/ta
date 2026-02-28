from laakhay.ta.expr.dsl import parse_expression_text
from laakhay.ta.expr.planner import plan_expression


def test_planner_volume_mean_requirements():
    """Test that mean(volume) only requires volume."""
    expr = parse_expression_text("mean(volume, 10)")
    plan = plan_expression(expr)
    print("VOLUME REQS:", [req for req in plan.requirements.data_requirements])

    # Check that 'volume' is required as a data requirement
    assert any(req.field == "volume" and req.source == "ohlcv" for req in plan.requirements.data_requirements)

    # Check that 'close' is NOT required
    assert not any(req.field == "close" for req in plan.requirements.data_requirements)


def test_planner_close_mean_requirements():
    """Test that mean(close) requires close."""
    expr = parse_expression_text("mean(close, 10)")
    plan = plan_expression(expr)
    print("CLOSE REQS:", [req for req in plan.requirements.data_requirements])

    assert any(req.field == "close" and req.source == "ohlcv" for req in plan.requirements.data_requirements)
