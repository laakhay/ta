"""Tests for laakhay.ta.core.bar module."""

import pytest
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

from laakhay.ta.core.bar import Bar


class TestBar:
    """Test Bar data model."""
    
    def test_bar_creation_and_validation(self, sample_datetime_utc: datetime) -> None:
        """Test bar creation and all validation rules."""
        # Valid bar using from_raw (handles coercion)
        bar = Bar.from_raw(ts=sample_datetime_utc, open=100, high=110, low=95, close=105, volume=1000, is_closed=True)
        assert bar.ts == sample_datetime_utc
        assert bar.open == Decimal("100")
        assert bar.is_closed is True
        
        # Validation: high < low
        with pytest.raises(ValueError, match="High must be >= low"):
            Bar.from_raw(ts=sample_datetime_utc, open=100, high=90, low=95, close=105, volume=1000, is_closed=True)
        
        # Validation: high < open/close
        with pytest.raises(ValueError, match="High must be >= open and close"):
            Bar.from_raw(ts=sample_datetime_utc, open=100, high=95, low=90, close=105, volume=1000, is_closed=True)
        
        # Validation: low > open/close
        with pytest.raises(ValueError, match="Low must be <= open and close"):
            Bar.from_raw(ts=sample_datetime_utc, open=100, high=110, low=105, close=95, volume=1000, is_closed=True)
        
        # Validation: negative volume
        with pytest.raises(ValueError, match="Volume must be >= 0"):
            Bar.from_raw(ts=sample_datetime_utc, open=100, high=110, low=95, close=105, volume=-1000, is_closed=True)
    
    def test_bar_properties(self, sample_datetime_utc: datetime) -> None:
        """Test all calculated properties."""
        bar = Bar.from_raw(ts=sample_datetime_utc, open=100, high=110, low=90, close=105, volume=1000, is_closed=True)
        
        assert bar.hlc3 == Decimal("101.6666666666666666666666667")  # (110+90+105)/3
        assert bar.ohlc4 == Decimal("101.25")  # (100+110+90+105)/4
        assert bar.hl2 == Decimal("100")  # (110+90)/2
        assert bar.body_size == Decimal("5")  # |105-100|
        assert bar.upper_wick == Decimal("5")  # 110-max(100,105)
        assert bar.lower_wick == Decimal("10")  # min(100,105)-90
        assert bar.total_range == Decimal("20")  # 110-90
    
    def test_bar_from_raw(self, sample_datetime_utc: datetime) -> None:
        """Test from_raw class method with coercion."""
        # Test with various input types
        bar = Bar.from_raw(ts=sample_datetime_utc, open=100, high=110, low=95, close=105, volume=1000, is_closed=True)
        assert bar.open == Decimal("100")
        assert bar.volume == Decimal("1000")
        
        # Test with string inputs
        bar_str = Bar.from_raw(ts=sample_datetime_utc, open="100.5", high="110.5", low="95.5", close="105.5", volume="1000.5", is_closed=True)
        assert bar_str.open == Decimal("100.5")
        assert bar_str.volume == Decimal("1000.5")
        
        # Test with float inputs
        bar_float = Bar.from_raw(ts=sample_datetime_utc, open=100.5, high=110.5, low=95.5, close=105.5, volume=1000.5, is_closed=True)
        assert bar_float.open == Decimal("100.5")
        assert bar_float.volume == Decimal("1000.5")
        
        # Test is_closed parameter
        bar_open = Bar.from_raw(ts=sample_datetime_utc, open=100.5, high=110, low=95, close=105, volume=1000, is_closed=False)
        assert bar_open.is_closed is False
    
    def test_bar_from_dict(self, sample_datetime_utc: datetime, sample_bar_dict: Dict[str, Any], sample_bar_dict_alternative_keys: Dict[str, Any], sample_bar_dict_short_keys: Dict[str, Any]) -> None:
        """Test from_dict with various key formats."""
        # Test standard keys
        bar1 = Bar.from_dict(sample_bar_dict)
        assert bar1.open == Decimal("100")
        
        # Test alternative keys
        bar2 = Bar.from_dict(sample_bar_dict_alternative_keys)
        assert bar2.open == Decimal("100")
        
        # Test short keys
        bar3 = Bar.from_dict(sample_bar_dict_short_keys)
        assert bar3.open == Decimal("100")
    
    def test_bar_repr(self, sample_datetime_utc: datetime) -> None:
        """Test string representation."""
        bar = Bar.from_raw(ts=sample_datetime_utc, open=100, high=110, low=95, close=105, volume=1000, is_closed=True)
        
        repr_str = repr(bar)
        assert "Bar(" in repr_str
        assert "o=100" in repr_str
        assert "h=110" in repr_str
        assert "l=95" in repr_str
        assert "c=105" in repr_str
        assert "vol=1000" in repr_str
        assert "closed=True" in repr_str
    
    def test_bar_edge_cases(self, sample_datetime_utc: datetime) -> None:
        """Test edge cases for properties."""
        # Doji candle (open == close)
        doji = Bar.from_raw(ts=sample_datetime_utc, open=100, high=105, low=95, close=100, volume=1000, is_closed=True)
        assert doji.body_size == Decimal("0")
        
        # Zero volume
        zero_vol = Bar.from_raw(ts=sample_datetime_utc, open=100, high=100, low=100, close=100, volume=0, is_closed=True)
        assert zero_vol.volume == Decimal("0")
        
        # Hammer candle (long lower wick)
        hammer = Bar.from_raw(ts=sample_datetime_utc, open=100, high=102, low=90, close=101, volume=1000, is_closed=True)
        assert hammer.lower_wick == Decimal("10")
        assert hammer.upper_wick == Decimal("1")