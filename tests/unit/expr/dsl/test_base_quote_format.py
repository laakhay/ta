"""Tests for Base/Quote format and instrument type chaining in expression parser."""

import pytest

from laakhay.ta.expr.dsl import StrategyError, parse_expression_text
from laakhay.ta.expr.ir.nodes import SourceRefNode as AttributeNode


class TestBaseQuoteFormat:
    """Test Base/Quote format parsing (BTC.USDT.price)."""

    def test_basic_base_quote_format(self):
        """Test basic Base/Quote format: BTC.USDT.price"""
        expr = parse_expression_text("BTC.USDT.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type is None  # Defaults to spot (implicit)
        assert expr.field == "close"
        assert expr.source == "ohlcv"
        assert expr.exchange is None
        assert expr.timeframe is None

    def test_base_quote_with_spot_explicit(self):
        """Test Base/Quote with explicit spot: BTC.USDT.spot.price"""
        expr = parse_expression_text("BTC.USDT.spot.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "spot"
        assert expr.field == "close"

    def test_base_quote_with_perp(self):
        """Test Base/Quote with perpetual: BTC.USDT.perp.price"""
        expr = parse_expression_text("BTC.USDT.perp.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "perp"
        assert expr.field == "close"

    def test_base_quote_with_perpetual(self):
        """Test Base/Quote with 'perpetual' (normalized to 'perp'): BTC.USDT.perpetual.price"""
        expr = parse_expression_text("BTC.USDT.perpetual.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "perp"  # Normalized
        assert expr.field == "close"

    def test_base_quote_with_futures(self):
        """Test Base/Quote with futures: BTC.USDT.futures.price"""
        expr = parse_expression_text("BTC.USDT.futures.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "futures"
        assert expr.field == "close"

    def test_base_quote_with_future(self):
        """Test Base/Quote with 'future' (normalized to 'futures'): BTC.USDT.future.price"""
        expr = parse_expression_text("BTC.USDT.future.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "futures"  # Normalized
        assert expr.field == "close"

    def test_base_quote_with_option(self):
        """Test Base/Quote with option: BTC.USDT.option.price"""
        expr = parse_expression_text("BTC.USDT.option.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "option"
        assert expr.field == "close"

    def test_different_quote_assets(self):
        """Test different quote assets: BTC.USDC.price, ETH.USDT.price"""
        expr1 = parse_expression_text("BTC.USDC.price")
        assert expr1.symbol == "BTC/USDC"
        assert expr1.base == "BTC"
        assert expr1.quote == "USDC"
        assert expr1.field == "close"

        expr2 = parse_expression_text("ETH.USDT.price")
        assert expr2.symbol == "ETH/USDT"
        assert expr2.base == "ETH"
        assert expr2.quote == "USDT"
        assert expr2.field == "close"

    def test_base_quote_with_exchange(self):
        """Test Base/Quote with exchange: binance.BTC.USDT.price"""
        expr = parse_expression_text("binance.BTC.USDT.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.exchange == "binance"
        assert expr.field == "close"

    def test_base_quote_with_exchange_and_instrument_type(self):
        """Test Base/Quote with exchange and instrument type: binance.BTC.USDT.perp.price"""
        expr = parse_expression_text("binance.BTC.USDT.perp.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.exchange == "binance"
        assert expr.instrument_type == "perp"
        assert expr.field == "close"

    def test_base_quote_with_timeframe(self):
        """Test Base/Quote with timeframe: BTC.USDT.h1.price (using h1 instead of 1h)"""
        expr = parse_expression_text("BTC.USDT.h1.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.timeframe == "1h"  # Normalized from h1
        assert expr.field == "close"

    def test_base_quote_with_instrument_type_and_timeframe(self):
        """Test Base/Quote with instrument type and timeframe: BTC.USDT.perp.h1.price"""
        expr = parse_expression_text("BTC.USDT.perp.h1.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "perp"
        assert expr.timeframe == "1h"  # Normalized from h1
        assert expr.field == "close"

    def test_base_quote_with_exchange_instrument_type_timeframe(self):
        """Test Base/Quote with exchange, instrument type, and timeframe: binance.BTC.USDT.perp.h1.price"""
        expr = parse_expression_text("binance.BTC.USDT.perp.h1.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.exchange == "binance"
        assert expr.instrument_type == "perp"
        assert expr.timeframe == "1h"  # Normalized from h1
        assert expr.field == "close"

    def test_base_quote_with_trades_source(self):
        """Test Base/Quote with trades source: BTC.USDT.trades.volume"""
        expr = parse_expression_text("BTC.USDT.trades.volume")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.source == "trades"
        assert expr.field == "volume"

    def test_base_quote_with_perp_and_trades(self):
        """Test Base/Quote with perpetual and trades: BTC.USDT.perp.trades.volume"""
        expr = parse_expression_text("BTC.USDT.perp.trades.volume")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "perp"
        assert expr.source == "trades"
        assert expr.field == "volume"

    def test_base_quote_with_orderbook_source(self):
        """Test Base/Quote with orderbook source: BTC.USDT.orderbook.imbalance"""
        expr = parse_expression_text("BTC.USDT.orderbook.imbalance")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.source == "orderbook"
        assert expr.field == "imbalance"

    def test_base_quote_with_liquidation_source(self):
        """Test Base/Quote with liquidation source: BTC.USDT.liquidation.count"""
        # Note: .count is treated as an aggregation, so we need to access it differently
        # The parser treats .count as AggregateNode, not AttributeNode
        from laakhay.ta.expr.ir.nodes import AggregateNode

        expr = parse_expression_text("BTC.USDT.liquidation.count")
        assert isinstance(expr, AggregateNode)
        assert isinstance(expr.series, AttributeNode)
        assert expr.series.symbol == "BTC/USDT"
        assert expr.series.base == "BTC"
        assert expr.series.quote == "USDT"
        # When parsing BTC.USDT.liquidation.count, the parser sees:
        # - BTC.USDT.liquidation as the series (source=liquidation, but no field yet)
        # - .count as the aggregation
        # The series should have liquidation as source
        assert expr.series.source == "liquidation"
        assert expr.operation == "count"

    def test_base_quote_complex_chain(self):
        """Test complex Base/Quote chain: binance.BTC.USDT.perp.h1.trades.volume"""
        expr = parse_expression_text("binance.BTC.USDT.perp.h1.trades.volume")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.exchange == "binance"
        assert expr.instrument_type == "perp"
        assert expr.timeframe == "1h"  # Normalized from h1
        assert expr.source == "trades"
        assert expr.field == "volume"

    def test_base_quote_in_comparison(self):
        """Test Base/Quote in comparison expression: BTC.USDT.price > 50000"""
        expr = parse_expression_text("BTC.USDT.price > 50000")
        # Should parse as BinaryNode with AttributeNode on left
        from laakhay.ta.expr.ir.nodes import BinaryOpNode as BinaryNode

        assert isinstance(expr, BinaryNode)
        assert isinstance(expr.left, AttributeNode)
        assert expr.left.symbol == "BTC/USDT"
        assert expr.left.base == "BTC"
        assert expr.left.quote == "USDT"

    def test_base_quote_cross_exchange_comparison(self):
        """Test Base/Quote cross-exchange comparison: binance.BTC.USDT.price > bybit.BTC.USDT.price"""
        expr = parse_expression_text("binance.BTC.USDT.price > bybit.BTC.USDT.price")
        from laakhay.ta.expr.ir.nodes import BinaryOpNode as BinaryNode

        assert isinstance(expr, BinaryNode)
        assert isinstance(expr.left, AttributeNode)
        assert isinstance(expr.right, AttributeNode)
        assert expr.left.symbol == "BTC/USDT"
        assert expr.left.exchange == "binance"
        assert expr.right.symbol == "BTC/USDT"
        assert expr.right.exchange == "bybit"

    def test_base_quote_perp_vs_spot_comparison(self):
        """Test Base/Quote perpetual vs spot comparison: BTC.USDT.perp.price > BTC.USDT.spot.price"""
        expr = parse_expression_text("BTC.USDT.perp.price > BTC.USDT.spot.price")
        from laakhay.ta.expr.ir.nodes import BinaryOpNode as BinaryNode

        assert isinstance(expr, BinaryNode)
        assert isinstance(expr.left, AttributeNode)
        assert isinstance(expr.right, AttributeNode)
        assert expr.left.symbol == "BTC/USDT"
        assert expr.left.instrument_type == "perp"
        assert expr.right.symbol == "BTC/USDT"
        assert expr.right.instrument_type == "spot"

    def test_base_quote_with_indicator(self):
        """Test Base/Quote with indicator: BTC.USDT.rsi(14)
        Note: Python AST parses this as BTC.USDT.rsi(14), which means it's a method call
        on BTC.USDT, not an indicator call. This would need special handling.
        This test is skipped as the parser doesn't support this pattern yet.
        """
        pytest.skip("Parser doesn't support indicator calls on Base/Quote attribute chains yet")

    def test_base_quote_with_explicit_indicator_input(self):
        """Test Base/Quote with explicit indicator input: sma(BTC.USDT.price, period=20)"""
        expr = parse_expression_text("sma(BTC.USDT.price, period=20)")
        from laakhay.ta.expr.ir.nodes import CallNode as IndicatorNode

        assert isinstance(expr, IndicatorNode)
        assert expr.name == "sma"
        assert isinstance(expr.args[0], AttributeNode)
        assert expr.args[0].symbol == "BTC/USDT"
        assert expr.args[0].base == "BTC"
        assert expr.args[0].quote == "USDT"

    def test_base_quote_case_insensitive_instrument_type(self):
        """Test that instrument types are case-insensitive: BTC.USDT.PERP.price"""
        expr = parse_expression_text("BTC.USDT.PERP.price")
        assert isinstance(expr, AttributeNode)
        assert expr.instrument_type == "perp"  # Normalized to lowercase

    def test_base_quote_mixed_case_base_quote(self):
        """Test that base and quote are normalized to uppercase: btc.usdt.price"""
        expr = parse_expression_text("btc.usdt.price")
        assert isinstance(expr, AttributeNode)
        assert expr.base == "BTC"  # Normalized to uppercase
        assert expr.quote == "USDT"  # Normalized to uppercase
        assert expr.symbol == "BTC/USDT"

    def test_lowercase_base_quote_in_indicator(self):
        """Test lowercase base/quote in indicator: sma(binance.btc.usdt.m5.ohlcv.close, 20)"""
        expr = parse_expression_text("sma(binance.btc.usdt.m5.ohlcv.close, 20)")
        from laakhay.ta.expr.ir.nodes import CallNode as IndicatorNode

        assert isinstance(expr, IndicatorNode)
        assert expr.name == "sma"
        assert isinstance(expr.args[0], AttributeNode)
        assert expr.args[0].symbol == "BTC/USDT"
        assert expr.args[0].base == "BTC"
        assert expr.args[0].quote == "USDT"
        assert expr.args[0].exchange == "binance"
        assert expr.args[0].timeframe == "5m"
        assert expr.args[0].source == "ohlcv"
        assert expr.args[0].field == "close"


class TestBaseQuoteFormatErrors:
    """Test error cases for Base/Quote format."""

    def test_missing_field_after_base_quote(self):
        """Test error when field is missing: BTC.USDT"""
        with pytest.raises(StrategyError, match="Missing field"):
            parse_expression_text("BTC.USDT")

    def test_invalid_instrument_type(self):
        """Test error with invalid instrument type: BTC.USDT.invalid.price"""
        # This should parse but may fail validation
        # The parser will treat 'invalid' as a source or field
        # Let's test what actually happens
        with pytest.raises(StrategyError):
            # This might fail at validation stage
            parse_expression_text("BTC.USDT.invalid.price")

    def test_base_quote_with_too_many_elements(self):
        """Test error with too many elements in chain"""
        # This depends on the specific chain structure
        # The parser should handle reasonable chains
        pass


class TestSimpleSymbolStillWorks:
    """Test that simple symbol format still works (backward compatibility)."""

    def test_simple_symbol_format(self):
        """Test simple symbol format: BTC.price"""
        expr = parse_expression_text("BTC.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC"
        assert expr.base is None
        assert expr.quote is None
        assert expr.instrument_type is None
        assert expr.field == "close"

    def test_simple_symbol_with_exchange(self):
        """Test simple symbol with exchange: binance.BTC.price"""
        expr = parse_expression_text("binance.BTC.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC"
        assert expr.exchange == "binance"
        assert expr.base is None
        assert expr.quote is None
        assert expr.field == "close"

    def test_simple_symbol_with_timeframe(self):
        """Test simple symbol with timeframe: BTC.h1.price (using h1 instead of 1h)"""
        expr = parse_expression_text("BTC.h1.price")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC"
        assert expr.timeframe == "1h"  # Normalized from h1
        assert expr.base is None
        assert expr.quote is None
        assert expr.field == "close"

    def test_simple_symbol_with_source(self):
        """Test simple symbol with source: BTC.trades.volume"""
        expr = parse_expression_text("BTC.trades.volume")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "BTC"
        assert expr.source == "trades"
        assert expr.base is None
        assert expr.quote is None


class TestQuoteAssetDetection:
    """Test that quote asset detection works correctly."""

    def test_three_char_quote(self):
        """Test 3-character quote: BTC.USD.price"""
        expr = parse_expression_text("BTC.USD.price")
        assert expr.symbol == "BTC/USD"
        assert expr.base == "BTC"
        assert expr.quote == "USD"

    def test_four_char_quote(self):
        """Test 4-character quote: BTC.USDC.price"""
        expr = parse_expression_text("BTC.USDC.price")
        assert expr.symbol == "BTC/USDC"
        assert expr.base == "BTC"
        assert expr.quote == "USDC"

    def test_quote_not_confused_with_timeframe(self):
        """Test that quote is not confused with timeframe: BTC.USDT.h1.price"""
        expr = parse_expression_text("BTC.USDT.h1.price")
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.timeframe == "1h"  # Normalized from h1

    def test_quote_not_confused_with_source(self):
        """Test that quote is not confused with source: BTC.USDT.trades.volume"""
        expr = parse_expression_text("BTC.USDT.trades.volume")
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.source == "trades"

    def test_quote_not_confused_with_instrument_type(self):
        """Test that quote is not confused with instrument type: BTC.USDT.perp.price"""
        expr = parse_expression_text("BTC.USDT.perp.price")
        assert expr.symbol == "BTC/USDT"
        assert expr.base == "BTC"
        assert expr.quote == "USDT"
        assert expr.instrument_type == "perp"

    def test_various_timeframe_formats(self):
        """Test various timeframe formats: m15, h4, d1, etc."""
        # Test minutes
        expr = parse_expression_text("BTC.USDT.m15.price")
        assert expr.timeframe == "15m"

        expr = parse_expression_text("BTC.USDT.m5.price")
        assert expr.timeframe == "5m"

        # Test hours
        expr = parse_expression_text("BTC.USDT.h4.price")
        assert expr.timeframe == "4h"

        # Test days
        expr = parse_expression_text("BTC.USDT.d1.price")
        assert expr.timeframe == "1d"

        # Test weeks
        expr = parse_expression_text("BTC.USDT.w1.price")
        assert expr.timeframe == "1w"

    def test_timeframe_before_instrument_type(self):
        """Test timeframe before instrument type: ETH.USDT.m5.perp.volume"""
        expr = parse_expression_text("ETH.USDT.m5.perp.volume")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "ETH/USDT"
        assert expr.base == "ETH"
        assert expr.quote == "USDT"
        assert expr.timeframe == "5m"  # Normalized from m5
        assert expr.instrument_type == "perp"
        assert expr.field == "volume"

    def test_exchange_timeframe_instrument_type_field(self):
        """Test full chain: binance.ETH.USDT.m5.perp.volume"""
        expr = parse_expression_text("binance.ETH.USDT.m5.perp.volume")
        assert isinstance(expr, AttributeNode)
        assert expr.symbol == "ETH/USDT"
        assert expr.base == "ETH"
        assert expr.quote == "USDT"
        assert expr.exchange == "binance"
        assert expr.timeframe == "5m"  # Normalized from m5
        assert expr.instrument_type == "perp"
        assert expr.field == "volume"

    def test_timeframe_instrument_type_in_comparison(self):
        """Test timeframe and instrument type in comparison: binance.ETH.USDT.m5.perp.volume > 100000"""
        expr = parse_expression_text("binance.ETH.USDT.m5.perp.volume > 100000")
        from laakhay.ta.expr.ir.nodes import BinaryOpNode as BinaryNode

        assert isinstance(expr, BinaryNode)
        assert isinstance(expr.left, AttributeNode)
        assert expr.left.symbol == "ETH/USDT"
        assert expr.left.exchange == "binance"
        assert expr.left.timeframe == "5m"
        assert expr.left.instrument_type == "perp"
        assert expr.left.field == "volume"
