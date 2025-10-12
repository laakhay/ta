"""Tests for core planner - DAG resolution and execution."""

from datetime import datetime, timezone

from laakhay.ta.core.plan import (
    ComputeRequest,
    ExecutionPlan,
    PlanNode,
    build_execution_plan,
    execute_plan,
)


class TestComputeRequest:
    """Test ComputeRequest validation and creation."""

    def test_valid_request(self):
        """Valid request should be created successfully."""
        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 20},
            symbols=["BTCUSDT"],
            eval_ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert req.indicator_name == "sma"
        assert req.params["period"] == 20
        assert "BTCUSDT" in req.symbols

    def test_empty_symbols(self):
        """Empty symbols list should be accepted (or validated by caller)."""
        from datetime import datetime, timezone

        # This test documents that empty symbols is currently allowed
        # Actual validation may be added later
        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 10},
            symbols=[],  # Empty list
            eval_ts=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        )

        # Currently this does not raise - just creates valid request
        assert req.symbols == []


class TestBuildExecutionPlan:
    """Test DAG construction and topological ordering."""

    def test_simple_indicator_plan(self):
        """Simple indicator should create minimal plan."""
        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 20},
            symbols=["BTCUSDT"],
            eval_ts=datetime.now(timezone.utc),
        )
        plan = build_execution_plan(req)

        assert isinstance(plan, ExecutionPlan)
        assert len(plan.nodes) >= 2  # At least raw + indicator nodes
        assert plan.nodes[0].kind == "raw"  # Raw data first
        assert plan.nodes[-1].kind == "indicator"  # Indicator last

    def test_multi_symbol_plan(self):
        """Multi-symbol request should create nodes per symbol."""
        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 20},
            symbols=["BTCUSDT", "ETHUSDT"],
            eval_ts=datetime.now(timezone.utc),
        )
        plan = build_execution_plan(req)

        # Should have raw nodes for both symbols
        raw_nodes = [n for n in plan.nodes if n.kind == "raw"]
        assert len(raw_nodes) == 2

    def test_topological_order(self):
        """Nodes should be in valid execution order."""
        req = ComputeRequest(
            indicator_name="macd",  # Composite indicator
            params={"fast": 12, "slow": 26, "signal": 9},
            symbols=["BTCUSDT"],
            eval_ts=datetime.now(timezone.utc),
        )
        plan = build_execution_plan(req)

        # Raw data should come before indicators
        raw_indices = [i for i, n in enumerate(plan.nodes) if n.kind == "raw"]
        indicator_indices = [i for i, n in enumerate(plan.nodes) if n.kind == "indicator"]

        assert all(r < i for r in raw_indices for i in indicator_indices)


class TestExecutePlan:
    """Test plan execution with real data."""

    def test_execute_simple_plan(self, sample_candles):
        """Execute simple SMA plan with sample data."""
        candles = sample_candles("BTCUSDT", count=30)

        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 20},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}

        result = execute_plan(plan, raw_cache, req)

        assert result.name == "sma"
        assert "BTCUSDT" in result.values
        assert len(result.values["BTCUSDT"]) > 0  # Should have SMA values

    def test_insufficient_data(self, sample_candles):
        """Plan execution with insufficient data should handle gracefully."""
        candles = sample_candles("BTCUSDT", count=5)  # Too few for SMA(20)

        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 20},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}

        result = execute_plan(plan, raw_cache, req)

        # Should return empty or handle gracefully
        assert result.name == "sma"
        assert len(result.values.get("BTCUSDT", [])) == 0


class TestPlanNode:
    """Test PlanNode data structure."""

    def test_node_creation(self):
        """PlanNode should be created with correct attributes."""
        node = PlanNode(
            kind="raw",
            key=("raw", "price", "close", "BTCUSDT"),
        )

        assert node.kind == "raw"
        assert node.key == ("raw", "price", "close", "BTCUSDT")

    def test_node_equality(self):
        """Nodes with same key should be equal."""
        node1 = PlanNode(kind="raw", key=("raw", "price", "close", "BTCUSDT"))
        node2 = PlanNode(kind="raw", key=("raw", "price", "close", "BTCUSDT"))

        assert node1.key == node2.key
