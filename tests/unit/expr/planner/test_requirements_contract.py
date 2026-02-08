
import pytest
from laakhay.ta.expr.dsl import compile_expression
from laakhay.ta.expr.planner.planner import plan_expression
from laakhay.ta.expr.dsl.parser import ExpressionParser

def test_requirements_contract_presence():
    """Verify that SignalRequirements includes data_requirements."""
    expr = compile_expression("mean(close, 10) > 100")
    reqs = expr.requirements()
    
    assert hasattr(reqs, "data_requirements")
    # Check that OHLCV requirement was emitted
    ohlcv_reqs = [r for r in reqs.data_requirements if r.source == "ohlcv"]
    assert len(ohlcv_reqs) >= 1
    close_req = next((r for r in ohlcv_reqs if r.field == "close"), None)
    assert close_req is not None
    assert close_req.min_lookback == 10

def test_requirements_dict_serialization():
    """Verify that PlanResult.to_dict() includes data_requirements."""
    from laakhay.ta.expr.dsl import compile_expression
    expr = compile_expression("close > 100")
    
    # We can get the plan from the Expression object's internal cache if we want to test to_dict
    plan = expr._ensure_plan()
    
    d = plan.to_dict()
    assert "requirements" in d
    req_dict = d["requirements"]
    
    # Verify ohlcv requirement in dict
    ohlcv_reqs = [r for r in req_dict["data_requirements"] if r["source"] == "ohlcv"]
    assert len(ohlcv_reqs) >= 1
    assert any(r["field"] == "close" for r in ohlcv_reqs)

def test_required_sources_and_exchanges_present():
    """Verify that data requirements are present."""
    expr = compile_expression("mean(close, 10) > 100")
    reqs = expr.requirements()
    
    assert isinstance(reqs.data_requirements, tuple)
    assert len(reqs.data_requirements) > 0
