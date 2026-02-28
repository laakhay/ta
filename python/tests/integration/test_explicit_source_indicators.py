"""Integration tests for explicit source indicators.

Tests indicators with explicit input expressions like sma(BTC.price, period=20)
and sma(trades.volume, period=20).
"""

from laakhay.ta.expr.dsl import compile_expression, parse_expression_text
from laakhay.ta.expr.ir.nodes import LiteralNode
from laakhay.ta.expr.planner import plan_expression


def _input_expr(node):
    """First positional arg when it's an expression (not a literal)."""
    if not node.args:
        return None
    first = node.args[0]
    return None if isinstance(first, LiteralNode) else first


class TestExplicitSourceIndicators:
    """Test indicators with explicit source expressions."""

    def test_sma_with_explicit_price(self, multi_source_dataset):
        """Test SMA with explicit price source."""
        # Parse: sma(BTC.price, period=20)
        expr_text = "sma(BTC.price, period=20)"
        expr = parse_expression_text(expr_text)

        # Verify explicit input expression is set (args[0] is source ref, not literal)
        assert _input_expr(expr) is not None
        assert expr.name == "sma"
        period_node = expr.kwargs.get("period")
        assert period_node is not None and period_node.value == 20

        # Compile and run
        compiled = compile_expression(expr)
        result = compiled.run(multi_source_dataset)

        series = result[("BTCUSDT", "1h", "default")]
        assert len(series.values) > 0

    def test_sma_with_explicit_trades_volume(self, multi_source_dataset):
        """Test SMA with explicit trades volume source."""
        # Parse: sma(BTC.trades.volume, period=10)
        expr_text = "sma(BTC.trades.volume, period=10)"
        expr = parse_expression_text(expr_text)

        assert _input_expr(expr) is not None

        # Compile and run
        compiled = compile_expression(expr)
        result = compiled.run(multi_source_dataset)

        series = result[("BTCUSDT", "1h", "default")]
        assert len(series.values) > 0

    def test_rsi_with_explicit_source(self, multi_source_dataset):
        """Test RSI with explicit source."""
        # Parse: rsi(BTC.price, period=14)
        expr_text = "rsi(BTC.price, period=14)"
        expr = parse_expression_text(expr_text)

        assert _input_expr(expr) is not None

        # Compile and run
        compiled = compile_expression(expr)
        result = compiled.run(multi_source_dataset)

        series = result[("BTCUSDT", "1h", "default")]
        assert len(series.values) > 0

    def test_plan_with_explicit_source(self):
        """Test that planning correctly tracks dependencies for explicit sources."""
        expr_text = "sma(BTC.trades.volume, period=20)"
        expr = parse_expression_text(expr_text)
        compiled = compile_expression(expr)
        plan = plan_expression(compiled._node)

        # Should require trades source
        assert any(req.source == "trades" for req in plan.requirements.data_requirements)

        # Should have data requirements for trades
        trades_reqs = [req for req in plan.requirements.data_requirements if req.source == "trades"]
        assert len(trades_reqs) > 0

    def test_nested_explicit_source(self, multi_source_dataset):
        """Test nested expressions with explicit sources."""
        # Parse: sma(BTC.price + BTC.trades.volume / 1000, period=10)
        expr_text = "sma(BTC.price + BTC.trades.volume / 1000, period=10)"
        expr = parse_expression_text(expr_text)

        assert _input_expr(expr) is not None

        # Compile and run
        compiled = compile_expression(expr)
        result = compiled.run(multi_source_dataset)

        series = result[("BTCUSDT", "1h", "default")]
        assert len(series.values) > 0

    def test_explicit_source_with_orderbook(self, multi_source_dataset):
        """Test indicator with explicit orderbook source."""
        # Parse: sma(BTC.orderbook.imbalance, period=5)
        expr_text = "sma(BTC.orderbook.imbalance, period=5)"
        expr = parse_expression_text(expr_text)

        assert _input_expr(expr) is not None

        # Compile and run
        compiled = compile_expression(expr)
        result = compiled.run(multi_source_dataset)

        series = result[("BTCUSDT", "1h", "default")]
        assert len(series.values) > 0

    def test_explicit_source_with_liquidation(self, multi_source_dataset):
        """Test indicator with explicit liquidation source."""
        # Parse: sma(BTC.liquidation.volume, period=5)
        expr_text = "sma(BTC.liquidation.volume, period=5)"
        expr = parse_expression_text(expr_text)

        assert _input_expr(expr) is not None

        # Compile and run
        compiled = compile_expression(expr)
        result = compiled.run(multi_source_dataset)

        series = result[("BTCUSDT", "1h", "default")]
        assert len(series.values) > 0

    def test_backwards_compatibility_no_explicit_source(self, multi_source_dataset):
        """Test that indicators without explicit sources still work (backwards compatibility)."""
        # Parse: sma(20) - should use default close price
        expr_text = "sma(20)"
        expr = parse_expression_text(expr_text)

        # No explicit input: args[0] is literal (period), not expression
        assert _input_expr(expr) is None

        # Compile and run
        compiled = compile_expression(expr)
        result = compiled.run(multi_source_dataset)

        series = result[("BTCUSDT", "1h", "default")]
        assert len(series.values) > 0
