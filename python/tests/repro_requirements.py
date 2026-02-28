from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.planner import plan_expression


def test_rma_tr_requirements():
    expr = compile_expression("rma(tr(), period=14)")
    plan = plan_expression(expr._node)

    print(f"\nRequirements: {plan.requirements}")

    # tr() requires high, low, close
    fields = {req.field for req in plan.requirements.data_requirements if req.source == "ohlcv"}
    assert "high" in fields
    assert "low" in fields
    assert "close" in fields


def test_mean_volume_requirements():
    expr = compile_expression("mean(volume, lookback=10)")
    plan = plan_expression(expr._node)

    print(f"\nRequirements: {plan.requirements}")

    fields = {req.field for req in plan.requirements.data_requirements if req.source == "ohlcv"}
    assert "volume" in fields


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
