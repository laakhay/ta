"""End-to-end tests demonstrating the complete laakhay-ta workflow."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from laakhay.ta import Bar, Engine, dataset, indicator
from laakhay.ta.core import OHLCV, Series
from laakhay.ta.core.types import Price
from laakhay.ta.expr.algebra.operators import _to_node
from laakhay.ta.expr.ir.nodes import BinaryOpNode, LiteralNode


class TestEndToEnd:
    """Test complete end-to-end workflows."""

    def test_complete_workflow(self):
        """Test complete workflow from data creation to indicator evaluation."""
        # 1. Create sample market data
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
                high=Price("115"),
                low=Price("108"),
                close=Price("114"),
                volume=Price("1400"),
                is_closed=True,
            ),
        ]

        # 2. Convert to OHLCV and create dataset
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")
        ds = dataset(ohlcv)

        # 3. Create indicators
        sma_2 = indicator("sma", period=2)
        sma_3 = indicator("sma", period=3)

        # 4. Test direct indicator execution
        sma_2_result = sma_2(ds)
        sma_3_result = sma_3(ds)

        # Verify SMA(2) results: full length 4
        assert len(sma_2_result.values) == 4
        # First value is padded/unavailable
        assert sma_2_result.availability_mask[0] is False
        assert sma_2_result.values[1] == Price(Decimal("104"))  # (102+106)/2
        assert sma_2_result.values[2] == Price(Decimal("108"))  # (106+110)/2
        assert sma_2_result.values[3] == Price(Decimal("112"))  # (110+114)/2

        # Verify SMA(3) results: full length 4
        assert len(sma_3_result.values) == 4
        assert sma_3_result.availability_mask[1] is False
        assert sma_3_result.values[2] == Price(Decimal("106"))  # (102+106+110)/3
        assert sma_3_result.values[3] == Price(Decimal("110"))  # (106+110+114)/3

        # 5. Test expression composition with Engine
        engine = Engine()

        # Create expression: SMA(2) + 10 (using same period to avoid alignment issues)
        sma_plus_10 = BinaryOpNode("add", _to_node(sma_2), LiteralNode(10))

        # Evaluate expression
        result = engine.evaluate(sma_plus_10, ds)

        # Verify result
        assert isinstance(result, Series)
        assert len(result.values) == 4  # Full length 4

        # First value (index 0) is warmup for SMA(2), so result is padded/None
        assert result.availability_mask[0] is False

        # Second value (index 1): 104 + 10 = 114
        assert result.values[1] == Price(Decimal("114"))
        # Third value (index 2): 108 + 10 = 118
        assert result.values[2] == Price(Decimal("118"))
        # Fourth value (index 3): 112 + 10 = 122
        assert result.values[3] == Price(Decimal("122"))

    def test_dataset_field_access(self):
        """Test accessing individual fields from dataset."""
        # Create sample data
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

        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")
        ds = dataset(ohlcv)

        # Test field access
        close_series = ds["close"]
        open_series = ds["open"]
        high_series = ds["high"]
        low_series = ds["low"]
        volume_series = ds["volume"]

        # Verify all series have correct values
        assert close_series.values == (Price(Decimal("102")), Price(Decimal("106")))
        assert open_series.values == (Price(Decimal("100")), Price(Decimal("102")))
        assert high_series.values == (Price(Decimal("105")), Price(Decimal("108")))
        assert low_series.values == (Price(Decimal("95")), Price(Decimal("98")))
        assert volume_series.values == (Price(Decimal("1000")), Price(Decimal("1200")))

    def test_complex_expression_workflow(self):
        """Test complex expression workflow with multiple indicators."""
        # Create sample data
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

        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")
        ds = dataset(ohlcv)

        # Create indicators
        sma_2 = indicator("sma", period=2)
        sma_3 = indicator("sma", period=3)

        # Create simple expression: SMA(2) > 105
        sma_gt_105 = BinaryOpNode("gt", _to_node(sma_2), LiteralNode(105))

        # Evaluate with engine
        engine = Engine()
        result = engine.evaluate(sma_gt_105, ds)

        # Verify result
        assert isinstance(result, Series)
        # Should have 3 results (Full length)
        assert len(result.values) == 3
        # Result should be boolean (True/False)
        assert all(val in (Price(Decimal("1")), Price(Decimal("0"))) for val in result.values)

        # First value is False (unavailable or 0)
        assert result.values[0] == Price(Decimal("0"))
        # SMA(2) at index 1 is 104 -> 104 > 105 = False (0)
        assert result.values[1] == Price(Decimal("0"))
        # SMA(2) at index 2 is 108 -> 108 > 105 = True (1)
        assert result.values[2] == Price(Decimal("1"))

    def test_error_handling_workflow(self):
        """Test error handling in complete workflow."""
        # Test with empty dataset
        empty_ds = dataset()
        sma_2 = indicator("sma", period=2)

        # Should raise error for empty dataset
        with pytest.raises(ValueError, match="SeriesContext has no series to operate on"):
            sma_2(empty_ds)

        # Test with insufficient data
        single_bar = [
            Bar(
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                open=Price("100"),
                high=Price("105"),
                low=Price("95"),
                close=Price("102"),
                volume=Price("1000"),
                is_closed=True,
            )
        ]

        ohlcv = OHLCV.from_bars(single_bar, symbol="BTCUSDT", timeframe="1h")
        ds = dataset(ohlcv)

        # SMA(2) on 1 bar should return full length series (1) with false mask
        result = sma_2(ds)
        assert isinstance(result, Series)
        assert len(result.values) == 1
        assert not result.availability_mask[0]
