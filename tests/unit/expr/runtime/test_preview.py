"""Tests for expression preview functionality."""

from datetime import UTC, datetime, timedelta

import pytest

from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr import PreviewResult, preview
from laakhay.ta.expr.dsl import StrategyError


def create_sample_bars(count: int = 50) -> list[dict]:
    """Create sample OHLCV bars for testing."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = []
    for i in range(count):
        bars.append(
            {
                "timestamp": base + timedelta(hours=i),
                "open": 100.0 + i,
                "high": 101.0 + i,
                "low": 99.0 + i,
                "close": 100.0 + i,
                "volume": 1000.0 + i,
                "is_closed": True,
            }
        )
    return bars


class TestPreviewBasic:
    """Test basic preview functionality."""

    def test_preview_with_bars(self):
        """Test preview with raw bars."""
        bars = create_sample_bars(50)
        result = preview("sma(20)", bars=bars, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, PreviewResult)
        assert result.series is not None
        assert len(result.series) > 0
        assert result.trim >= 20
        assert len(result.indicators) == 1
        assert result.indicators[0].name == "sma"

    def test_preview_with_dataset(self):
        """Test preview with pre-built dataset."""
        base = datetime(2024, 1, 1, tzinfo=UTC)
        bars = [Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i) for i in range(50)]
        ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")
        dataset = Dataset()
        dataset.add_series("BTCUSDT", "1h", ohlcv)

        result = preview("sma(20)", dataset=dataset)

        assert isinstance(result, PreviewResult)
        assert result.series is not None
        assert len(result.series) > 0

    def test_preview_boolean_expression_triggers(self):
        """Test preview extracts triggers from boolean expressions."""
        bars = create_sample_bars(50)
        # Create an expression that should have some True values
        # sma(5) > sma(10) will be True when fast MA is above slow MA
        result = preview("sma(5) > sma(10)", bars=bars, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, PreviewResult)
        assert isinstance(result.triggers, list)
        # Should have some triggers (True values)

    def test_preview_complex_expression(self):
        """Test preview with complex nested expression."""
        bars = create_sample_bars(100)  # Need more bars for RSI(14) + SMA(50)
        result = preview("(sma(20) > sma(50)) and (rsi(14) < 30)", bars=bars, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result, PreviewResult)
        assert len(result.indicators) == 3  # sma, sma, rsi
        assert result.trim >= 50  # Largest lookback

    def test_preview_missing_symbol_timeframe(self):
        """Test preview raises error when bars provided without symbol/timeframe."""
        bars = create_sample_bars(50)
        with pytest.raises(ValueError, match="Must provide 'symbol' and 'timeframe'"):
            preview("sma(20)", bars=bars)

    def test_preview_missing_input(self):
        """Test preview raises error when neither bars nor dataset provided."""
        with pytest.raises(ValueError, match="Must provide either 'bars' or 'dataset'"):
            preview("sma(20)")

    def test_preview_invalid_expression(self):
        """Test preview raises error for invalid expression."""
        bars = create_sample_bars(50)
        with pytest.raises(StrategyError):
            preview("invalid_func(20)", bars=bars, symbol="BTCUSDT", timeframe="1h")


class TestPreviewTriggers:
    """Test trigger extraction functionality."""

    def test_preview_boolean_triggers(self):
        """Test that boolean expressions produce triggers."""
        bars = create_sample_bars(30)
        # Simple comparison that should produce boolean results
        result = preview("close > 100", bars=bars, symbol="BTCUSDT", timeframe="1h")

        assert isinstance(result.triggers, list)
        # Since all closes are >= 100, should have triggers
        assert len(result.triggers) > 0
        for trigger in result.triggers:
            assert "timestamp" in trigger
            assert "value" in trigger
            assert trigger["value"] is True

    def test_preview_no_triggers_for_numeric(self):
        """Test that numeric expressions don't produce triggers."""
        bars = create_sample_bars(30)
        result = preview("sma(10)", bars=bars, symbol="BTCUSDT", timeframe="1h")

        # Numeric expression shouldn't have triggers
        assert len(result.triggers) == 0

    def test_preview_trigger_structure(self):
        """Test trigger structure is correct."""
        bars = create_sample_bars(30)
        result = preview("close > 95", bars=bars, symbol="BTCUSDT", timeframe="1h")

        if result.triggers:
            trigger = result.triggers[0]
            assert "timestamp" in trigger
            assert "value" in trigger
            assert "index" in trigger
            assert isinstance(trigger["value"], bool)


class TestPreviewTrim:
    """Test dataset trimming functionality."""

    def test_preview_applies_trim(self):
        """Test that preview applies correct trim based on indicator lookback."""
        bars = create_sample_bars(100)
        result = preview("sma(50)", bars=bars, symbol="BTCUSDT", timeframe="1h")

        assert result.trim >= 50
        # After trim, should still have data
        assert len(result.series) > 0
        # Should have fewer values than original (100 - trim)
        assert len(result.series) <= (100 - result.trim)

    def test_preview_multiple_indicators_trim(self):
        """Test trim uses largest lookback from all indicators."""
        bars = create_sample_bars(100)
        # sma(20) needs 20, sma(50) needs 50, so trim should be >= 50
        result = preview("sma(20) > sma(50)", bars=bars, symbol="BTCUSDT", timeframe="1h")

        assert result.trim >= 50
