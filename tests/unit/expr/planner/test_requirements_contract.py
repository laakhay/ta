
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

def test_nested_indicator_requirements_golden():
    """Verify golden requirements for nested indicators rma(tr())."""
    expr = compile_expression("rma(tr(), period=14) > 50")
    reqs = expr.requirements()
    
    # tr() requires high, low, close. rma(tr, 14) requires 14+1-1=14 shift of tr,
    # but tr has a lookback of 2 (for hp/lp), so we need 14+1=15 bars.
    data_reqs = sorted(reqs.data_requirements, key=lambda r: r.field)
    assert len(data_reqs) == 3
    
    fields = [r.field for r in data_reqs]
    assert fields == ["close", "high", "low"]
    for r in data_reqs:
        assert r.source == "ohlcv"
        assert r.min_lookback == 15

def test_multi_source_requirements_golden():
    """Verify requirements for multi-source expressions."""
    expr = compile_expression("BTC.trades.volume > mean(volume, 10)")
    reqs = expr.requirements()
    
    # Should have volume from trades (for BTC) and volume from ohlcv (default context)
    vol_trades = next(r for r in reqs.data_requirements if r.source == "trades")
    vol_ohlcv = next(r for r in reqs.data_requirements if r.source == "ohlcv")
    
    assert vol_trades.symbol == "BTC"
    assert vol_trades.field == "volume"
    assert vol_trades.min_lookback == 1
    
    assert vol_ohlcv.symbol is None
    assert vol_ohlcv.field == "volume"
    assert vol_ohlcv.min_lookback == 10

def test_exchange_qualified_requirements_golden():
    """Verify requirements for exchange-qualified expressions."""
    expr = compile_expression("binance.ETH.ohlcv.close > 2000")
    reqs = expr.requirements()
    
    assert len(reqs.data_requirements) == 1
    req = reqs.data_requirements[0]
    assert req.exchange == "binance"
    assert req.symbol == "ETH"
    assert req.source == "ohlcv"
    assert req.field == "close"
    assert req.min_lookback == 1
