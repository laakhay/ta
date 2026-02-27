"""Functional tests for indicator execution with Engine."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta import Bar, Engine, dataset, indicator
from laakhay.ta.core import OHLCV, Series
from laakhay.ta.core.types import Price


class TestIndicatorsFunctional:
    """Test indicators with real data and Engine evaluation."""

    def test_sma_indicator_execution(self):
        """Test SMA indicator execution with real data."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 3, tzinfo=UTC),
                open=Price("106"),
                high=Price("112"),
                low=Price("104"),
                close=Price("110"),
                volume=Price("1300"),
                is_closed=True,
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Create SMA indicator handle
        sma_2 = indicator("sma", period=2)

        # Test that we can get the schema
        schema = sma_2.schema
        assert schema["name"] == "sma"
        # Check that period parameter exists
        assert "period" in schema["params"]

        # Test indicator execution
        result = sma_2(ds)

        # Verify result
        assert isinstance(result, Series)
        assert len(result.values) == 3  # Full length 3
        # First SMA is at index 1: (102 + 106) / 2 = 104
        assert result.availability_mask[0] is False
        assert result.values[1] == Price(Decimal("104"))
        # Second SMA: (106 + 110) / 2 = 108
        assert result.values[2] == Price(Decimal("108"))

    def test_indicator_with_engine(self):
        """Test indicator execution through Engine."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Create SMA indicator handle
        sma_2 = indicator("sma", period=2)

        # Test that indicator handle can be used as expression
        from laakhay.ta.expr.algebra.operators import _to_node
        from laakhay.ta.expr.ir.nodes import BinaryOpNode, LiteralNode

        # Create expression: sma + 10
        add_expr = BinaryOpNode("add", _to_node(sma_2), LiteralNode(10))

        # Evaluate with engine
        engine = Engine()
        result = engine.evaluate(add_expr, ds)

        # Verify result
        assert isinstance(result, Series)
        assert len(result.values) == 2  # SMA(2) on 2 bars = full length 2
        # SMA: (102 + 106) / 2 = 104, + 10 = 114 at index 1
        assert result.values[1] == Price(Decimal("114"))

    def test_multiple_indicators(self):
        """Test multiple indicators on same dataset."""
        # Create sample bars
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 3, tzinfo=UTC),
                open=Price("106"),
                high=Price("112"),
                low=Price("104"),
                close=Price("110"),
                volume=Price("1300"),
                is_closed=True,
            ),
        ]

        # Convert bars to OHLCV
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")

        # Create dataset from OHLCV
        ds = dataset(ohlcv)

        # Create multiple indicators
        sma_2 = indicator("sma", period=2)
        sma_3 = indicator("sma", period=3)

        # Test both indicators
        result_2 = sma_2(ds)
        result_3 = sma_3(ds)

        # Verify results
        assert isinstance(result_2, Series)
        assert isinstance(result_3, Series)
        assert len(result_2.values) == 3  # Full length 3
        assert len(result_3.values) == 3  # Full length 3

        # SMA(2) first result at index 1: (102 + 106) / 2 = 104
        assert result_2.values[1] == Price(Decimal("104"))
        # SMA(3) result at index 2: (102 + 106 + 110) / 3 = 106
        assert result_3.values[2] == Price(Decimal("106"))

    def test_indicator_error_handling(self):
        """Test indicator error handling."""
        # Create empty dataset
        ds = dataset()

        # Create SMA indicator
        sma_2 = indicator("sma", period=2)

        # Test that indicator raises appropriate error for empty dataset
        with pytest.raises(ValueError, match="SeriesContext has no series to operate on"):
            sma_2(ds)

    def test_rust_backed_momentum_volatility_indicators(self):
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 3, tzinfo=UTC),
                open=Price("106"),
                high=Price("112"),
                low=Price("104"),
                close=Price("110"),
                volume=Price("1300"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 4, tzinfo=UTC),
                open=Price("110"),
                high=Price("113"),
                low=Price("107"),
                close=Price("111"),
                volume=Price("1100"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 5, tzinfo=UTC),
                open=Price("111"),
                high=Price("114"),
                low=Price("109"),
                close=Price("112"),
                volume=Price("1000"),
                is_closed=True,
            ),
        ]

        ds = dataset(OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h"))

        rsi_handle = indicator("rsi", period=3)
        atr_handle = indicator("atr", period=3)
        stoch_handle = indicator("stochastic", k_period=3, d_period=2)

        rsi_res = rsi_handle(ds)
        atr_res = atr_handle(ds)
        stoch_k, stoch_d = stoch_handle(ds)

        assert len(rsi_res.values) == len(bars)
        assert len(atr_res.values) == len(bars)
        assert len(stoch_k.values) == len(bars)
        assert len(stoch_d.values) == len(bars)

        assert any(rsi_res.availability_mask)
        assert any(atr_res.availability_mask)
        assert any(stoch_k.availability_mask)
        assert any(stoch_d.availability_mask)

    def test_rust_backed_volume_indicators(self):
        bars = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 2, tzinfo=UTC),
                open=Price("102"),
                high=Price("108"),
                low=Price("98"),
                close=Price("106"),
                volume=Price("1200"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 3, tzinfo=UTC),
                open=Price("106"),
                high=Price("112"),
                low=Price("104"),
                close=Price("110"),
                volume=Price("1300"),
                is_closed=True,
            ),
            Bar(
                ts=datetime(2024, 1, 4, tzinfo=UTC),
                open=Price("110"),
                high=Price("113"),
                low=Price("107"),
                close=Price("109"),
                volume=Price("900"),
                is_closed=True,
            ),
        ]

        ds = dataset(OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h"))
        obv_res = indicator("obv")(ds)
        cmf_res = indicator("cmf", period=3)(ds)
        klinger_res, signal_res = indicator("klinger", fast_period=2, slow_period=3, signal_period=2)(ds)

        assert len(obv_res.values) == len(bars)
        assert len(cmf_res.values) == len(bars)
        assert len(klinger_res.values) == len(bars)
        assert len(signal_res.values) == len(bars)
        assert any(obv_res.availability_mask)
