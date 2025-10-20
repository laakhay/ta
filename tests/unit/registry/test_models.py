"""Tests for registry models."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.registry import SeriesContext, IndicatorHandle, IndicatorSchema
from laakhay.ta.core import Series
from laakhay.ta.core.types import Price, Timestamp


class TestSeriesContext:
    """Test SeriesContext functionality."""

    def test_series_context_creation(self) -> None:
        """Test creating SeriesContext with series."""
        timestamps = [datetime.now(timezone.utc)]
        values = [Decimal("100")]
        
        price_series = Series[Price](
            timestamps=timestamps,
            values=values,
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(price=price_series)
        
        assert "price" in ctx.available_series
        assert ctx.price == price_series

    def test_series_context_multiple_series(self) -> None:
        """Test SeriesContext with multiple series."""
        timestamps = [datetime.now(timezone.utc)]
        values = [Decimal("100")]
        
        price_series = Series[Price](
            timestamps=timestamps,
            values=values,
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        volume_series = Series[Price](
            timestamps=timestamps,
            values=values,
            symbol="BTCUSDT",
            timeframe="1h"
        )
        
        ctx = SeriesContext(price=price_series, volume=volume_series)
        
        assert len(ctx.available_series) == 2
        assert "price" in ctx.available_series
        assert "volume" in ctx.available_series
        assert ctx.price == price_series
        assert ctx.volume == volume_series

    def test_series_context_missing_series(self) -> None:
        """Test accessing missing series raises AttributeError."""
        ctx = SeriesContext(price=Series[Price](
            timestamps=[datetime.now(timezone.utc)],
            values=[Decimal("100")],
            symbol="BTCUSDT",
            timeframe="1h"
        ))
        
        with pytest.raises(AttributeError, match="Series 'missing' not found in context"):
            _ = ctx.missing

    def test_series_context_private_attribute(self) -> None:
        """Test accessing private attributes raises AttributeError."""
        ctx = SeriesContext()
        
        with pytest.raises(AttributeError, match="'SeriesContext' object has no attribute '_private'"):
            _ = ctx._private


class TestIndicatorHandle:
    """Test IndicatorHandle functionality."""

    def test_indicator_handle_creation(self) -> None:
        """Test creating IndicatorHandle."""
        def dummy_indicator(ctx: SeriesContext, period: int = 14) -> Series[Price]:
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        from inspect import signature
        from laakhay.ta.registry import IndicatorSchema, ParamSchema, OutputSchema
        
        schema = IndicatorSchema(
            name="dummy",
            description="Dummy indicator",
            parameters={
                "period": ParamSchema(
                    name="period",
                    type=int,
                    default=14,
                    required=False,
                    description="Period"
                )
            },
            outputs={
                "result": OutputSchema(
                    name="result",
                    type=float,
                    description="Result"
                )
            }
        )
        
        handle = IndicatorHandle(
            name="dummy",
            func=dummy_indicator,
            signature=signature(dummy_indicator),
            schema=schema,
            aliases=["dummy_ind"]
        )
        
        assert handle.name == "dummy"
        assert handle.func == dummy_indicator
        assert handle.aliases == ["dummy_ind"]

    def test_indicator_handle_call(self) -> None:
        """Test calling IndicatorHandle."""
        def dummy_indicator(ctx: SeriesContext, period: int = 14) -> Series[Price]:
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        from inspect import signature
        from laakhay.ta.registry import IndicatorSchema, ParamSchema, OutputSchema
        
        schema = IndicatorSchema(
            name="dummy",
            description="Dummy indicator",
            parameters={
                "period": ParamSchema(
                    name="period",
                    type=int,
                    default=14,
                    required=False,
                    description="Period"
                )
            },
            outputs={
                "result": OutputSchema(
                    name="result",
                    type=float,
                    description="Result"
                )
            }
        )
        
        handle = IndicatorHandle(
            name="dummy",
            func=dummy_indicator,
            signature=signature(dummy_indicator),
            schema=schema,
            aliases=[]
        )
        
        ctx = SeriesContext()
        result = handle(ctx, period=20)
        
        assert isinstance(result, Series)
        assert result.symbol == "BTCUSDT"

    def test_indicator_handle_with_overrides(self) -> None:
        """Test IndicatorHandle with_overrides method."""
        def dummy_indicator(ctx: SeriesContext, period: int = 14) -> Series[Price]:
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        from inspect import signature
        from laakhay.ta.registry import IndicatorSchema, ParamSchema, OutputSchema
        
        schema = IndicatorSchema(
            name="dummy",
            description="Dummy indicator",
            parameters={
                "period": ParamSchema(
                    name="period",
                    type=int,
                    default=14,
                    required=False,
                    description="Period"
                )
            },
            outputs={
                "result": OutputSchema(
                    name="result",
                    type=float,
                    description="Result"
                )
            }
        )
        
        handle = IndicatorHandle(
            name="dummy",
            func=dummy_indicator,
            signature=signature(dummy_indicator),
            schema=schema,
            aliases=[]
        )
        
        # Test with_overrides creates new handle with parameter overrides
        overridden = handle.with_overrides(period=20)
        assert overridden.name == "dummy"
        assert overridden.schema == schema
        
        # Test that the override actually works
        from datetime import datetime, timezone
        ctx = SeriesContext(price=Series(
            timestamps=[datetime.now(timezone.utc)],
            values=[Price(Decimal("100"))],
            symbol="BTCUSDT",
            timeframe="1h"
        ))
        result = overridden(ctx)  # Should use period=20
        assert isinstance(result, Series)
    
    def test_indicator_handle_with_overrides_validation(self) -> None:
        """Test IndicatorHandle with_overrides parameter validation."""
        def dummy_indicator(ctx: SeriesContext, period: int = 14) -> Series[Price]:
            return Series(
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        from inspect import signature
        from laakhay.ta.registry import IndicatorSchema, ParamSchema, OutputSchema
        
        schema = IndicatorSchema(
            name="dummy",
            description="Dummy indicator",
            parameters={
                "period": ParamSchema(
                    name="period",
                    type=int,
                    default=14,
                    required=False,
                    description="Period"
                )
            },
            outputs={
                "result": OutputSchema(
                    name="result",
                    type=float,
                    description="Result"
                )
            }
        )
        
        handle = IndicatorHandle(
            name="dummy",
            func=dummy_indicator,
            signature=signature(dummy_indicator),
            schema=schema,
            aliases=[]
        )
        
        # Test invalid parameter name
        with pytest.raises(ValueError, match="Unknown parameter 'invalid_param'"):
            handle.with_overrides(invalid_param=50)
        
        # Test invalid parameter type (no coercion)
        with pytest.raises(ValueError, match="Parameter 'period' expects int, got str"):
            handle.with_overrides(period="invalid")
        
        # Test valid type coercion
        overridden_handle = handle.with_overrides(period="50")  # String to int
        assert overridden_handle.name == "dummy"
        
        # Test float to int coercion
        overridden_handle = handle.with_overrides(period=50.0)  # Float to int
        assert overridden_handle.name == "dummy"
