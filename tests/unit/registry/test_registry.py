"""Tests for registry functionality."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from laakhay.ta.registry import Registry, register, indicator, describe_indicator, SeriesContext, IndicatorSchema, list_indicators, list_all_names, get_global_registry
from laakhay.ta.core import Series
from laakhay.ta.core.types import Price, Timestamp


class TestRegistry:
    """Test Registry functionality."""

    def test_registry_creation(self) -> None:
        """Test creating empty registry."""
        registry = Registry()
        assert len(registry.list_indicators()) == 0

    def test_register_indicator(self) -> None:
        """Test registering an indicator."""
        registry = Registry()
        
        def sma_indicator(ctx, period: int = 20) -> Series[Price]:
            """Simple Moving Average indicator."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        registry.register(sma_indicator, name="sma")
        
        assert "sma" in registry.list_indicators()
        handle = registry.get("sma")
        assert handle is not None
        assert handle.name == "sma"
        assert handle.func == sma_indicator

    def test_register_indicator_with_aliases(self) -> None:
        """Test registering indicator with aliases."""
        registry = Registry()
        
        def sma_indicator(ctx, period: int = 20) -> Series[Price]:
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        registry.register(sma_indicator, name="sma", aliases=["simple_ma", "moving_average"])
        
        # Test accessing by alias
        handle1 = registry.get("simple_ma")
        handle2 = registry.get("moving_average")
        handle3 = registry.get("sma")
        
        assert handle1 is handle2
        assert handle2 is handle3
        assert handle1.name == "sma"

    def test_register_duplicate_alias_conflict(self) -> None:
        """Test registering alias that conflicts with existing indicator."""
        registry = Registry()
        
        def indicator1(ctx) -> Series[Price]:
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        def indicator2(ctx) -> Series[Price]:
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        registry.register(indicator1, name="ind1")
        
        with pytest.raises(ValueError, match="Alias 'ind1' conflicts with existing indicator"):
            registry.register(indicator2, name="ind2", aliases=["ind1"])

    def test_get_nonexistent_indicator(self) -> None:
        """Test getting non-existent indicator returns None."""
        registry = Registry()
        assert registry.get("nonexistent") is None

    def test_build_schema_from_function(self) -> None:
        """Test schema building from function signature."""
        registry = Registry()
        
        def test_indicator(
            ctx: SeriesContext, 
            period: int = 20, 
            method: str = "sma",
            enabled: bool = True
        ) -> Series[Price]:
            """Test indicator with various parameter types."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        schema = registry._build_schema(test_indicator, "test", "Test indicator")
        
        assert schema.name == "test"
        assert schema.description == "Test indicator"
        assert len(schema.parameters) == 3
        assert "period" in schema.parameters
        assert "method" in schema.parameters
        assert "enabled" in schema.parameters
        
        # Check parameter details
        period_param = schema.parameters["period"]
        assert period_param.type == int
        assert period_param.default == 20
        assert period_param.required is False
        
        method_param = schema.parameters["method"]
        assert method_param.type == str
        assert method_param.default == "sma"
        assert method_param.required is False
        
        enabled_param = schema.parameters["enabled"]
        assert enabled_param.type == bool
        assert enabled_param.default is True
        assert enabled_param.required is False

    def test_build_schema_required_parameters(self) -> None:
        """Test schema building with required parameters."""
        registry = Registry()
        
        def test_indicator(ctx: SeriesContext, period: int, method: str) -> Series[Price]:
            """Test indicator with required parameters."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        schema = registry._build_schema(test_indicator, "test", "Test indicator")
        
        assert len(schema.parameters) == 2
        assert schema.parameters["period"].required is True
        assert schema.parameters["method"].required is True
        assert schema.parameters["period"].default is None
        assert schema.parameters["method"].default is None


class TestDecorator:
    """Test @register decorator functionality."""

    def test_register_decorator(self) -> None:
        """Test @register decorator."""
        @register(name="my_sma")
        def my_sma(ctx, period: int = 20) -> Series[Price]:
            """My custom SMA indicator."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        handle = indicator("my_sma")
        assert handle.name == "my_sma"
        # Note: handle.func will be the registered function, not necessarily the same object

    def test_register_decorator_default_name(self) -> None:
        """Test @register decorator with default function name."""
        @register()
        def default_name_indicator(ctx, period: int = 20) -> Series[Price]:
            """Indicator with default name."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        handle = indicator("default_name_indicator")
        assert handle.name == "default_name_indicator"

    def test_register_decorator_with_aliases(self) -> None:
        """Test @register decorator with aliases."""
        @register(name="ema", aliases=["exponential_ma", "exp_moving_avg"])
        def ema_indicator(ctx, period: int = 12) -> Series[Price]:
            """Exponential Moving Average."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        # Test accessing by name
        handle1 = indicator("ema")
        # Test accessing by aliases
        handle2 = indicator("exponential_ma")
        handle3 = indicator("exp_moving_avg")
        
        assert handle1.name == handle2.name  # Same indicator, different aliases
        assert handle2.name == handle3.name  # Same indicator, different aliases
        assert handle1.name == "ema"

    def test_register_decorator_with_description(self) -> None:
        """Test @register decorator with custom description."""
        @register(name="rsi", description="Relative Strength Index indicator")
        def rsi_indicator(ctx, period: int = 14) -> Series[Price]:
            """This docstring should be overridden."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        schema = describe_indicator("rsi")
        assert schema.description == "Relative Strength Index indicator"


class TestIndicatorAccessor:
    """Test indicator() and describe_indicator() functions."""

    def test_indicator_function(self) -> None:
        """Test indicator() function."""
        @register(name="test_indicator")
        def test_indicator(ctx, param: int = 10) -> Series[Price]:
            """Test indicator."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        handle = indicator("test_indicator")
        assert handle.name == "test_indicator"
        
        # Test with overrides (creates new handle with parameter overrides)
        overridden = handle.with_overrides(param=20)
        assert overridden.name == handle.name  # Same indicator with overrides

    def test_indicator_nonexistent(self) -> None:
        """Test indicator() with non-existent name."""
        with pytest.raises(ValueError, match="Indicator 'nonexistent' not found"):
            indicator("nonexistent")

    def test_describe_indicator(self) -> None:
        """Test describe_indicator() function."""
        @register(name="describe_test")
        def describe_test(ctx: SeriesContext, period: int = 14, method: str = "sma") -> Series[Price]:
            """Test indicator for description."""
            return Series[Price](
                timestamps=[datetime.now(timezone.utc)],
                values=[Decimal("100")],
                symbol="BTCUSDT",
                timeframe="1h"
            )
        
        schema = describe_indicator("describe_test")
        
        assert isinstance(schema, IndicatorSchema)
        assert schema.name == "describe_test"
        assert schema.description == "Test indicator for description."
        assert len(schema.parameters) == 2
        assert "period" in schema.parameters
        assert "method" in schema.parameters

    def test_describe_indicator_nonexistent(self) -> None:
        """Test describe_indicator() with non-existent name."""
        with pytest.raises(ValueError, match="Indicator 'nonexistent' not found"):
            describe_indicator("nonexistent")


class TestPublicAPI:
    """Test public API functions."""
    
    def test_list_indicators_function(self) -> None:
        """Test list_indicators() function."""
        # Register a test indicator
        @register("list_test", description="Test for listing")
        def test_indicator(ctx: SeriesContext, period: int = 20) -> Series[Price]:
            """Test indicator for listing."""
            return Series([(Timestamp(0), Price(Decimal("100")))])
        
        result = list_indicators()
        assert "list_test" in result
    
    def test_list_all_names_function(self) -> None:
        """Test list_all_names() function."""
        # Register a test indicator with alias
        @register("alias_test", aliases=["alias"], description="Test for aliases")
        def test_indicator_alias(ctx: SeriesContext, period: int = 20) -> Series[Price]:
            """Test indicator for aliases."""
            return Series([(Timestamp(0), Price(Decimal("100")))])
        
        result = list_all_names()
        assert "alias_test" in result
        assert "alias" in result


class TestValidation:
    """Test function validation during registration."""
    
    def test_validate_function_missing_series_context(self) -> None:
        """Test validation of function without SeriesContext parameter."""
        registry = Registry()
        
        def bad_function(period: int) -> Series[Price]:
            return Series([(Timestamp(0), Price(Decimal("100")))])
        
        with pytest.raises(ValueError, match="Indicator function 'bad_function' first parameter must be SeriesContext"):
            registry.register(bad_function)
    
    def test_validate_function_wrong_return_type(self) -> None:
        """Test validation of function with wrong return type."""
        registry = Registry()
        
        def bad_function(ctx: SeriesContext, period: int) -> int:
            return 42
        
        with pytest.raises(ValueError, match="Indicator function 'bad_function' must return Series"):
            registry.register(bad_function)
    
    def test_validate_function_no_parameters(self) -> None:
        """Test validation of function with no parameters."""
        registry = Registry()
        
        def bad_function() -> Series[Price]:
            return Series([(Timestamp(0), Price(Decimal("100")))])
        
        with pytest.raises(ValueError, match="Indicator function 'bad_function' must have at least one parameter"):
            registry.register(bad_function)


class TestComplexTypes:
    """Test support for complex type annotations."""
    
    def test_union_types(self) -> None:
        """Test Union type handling in schema building."""
        from typing import Union
        
        registry = Registry()
        
        def test_union(ctx: SeriesContext, value: Union[int, float]) -> Series[Price]:
            """Test indicator with Union parameter."""
            return Series([(Timestamp(0), Price(Decimal("100")))])
        
        registry.register(test_union, name="union_test")
        schema = registry.get("union_test").schema
        assert "value" in schema.parameters
        # Union types should be handled gracefully
    
    def test_optional_types(self) -> None:
        """Test Optional type handling."""
        from typing import Optional
        
        registry = Registry()
        
        def test_optional(ctx: SeriesContext, period: Optional[int] = 20) -> Series[Price]:
            """Test indicator with Optional parameter."""
            return Series([(Timestamp(0), Price(Decimal("100")))])
        
        registry.register(test_optional, name="optional_test")
        schema = registry.get("optional_test").schema
        assert "period" in schema.parameters
        assert not schema.parameters["period"].required


class TestMultiOutput:
    """Test multi-output indicator support."""
    
    def test_tuple_return_type(self) -> None:
        """Test tuple return type for multi-output indicators."""
        from typing import Tuple
        
        registry = Registry()
        
        def test_multi_output(ctx: SeriesContext, period: int) -> Tuple[Series[Price], Series[Price]]:
            """Test indicator with tuple return type."""
            return Series([(Timestamp(0), Price(Decimal("100")))]), Series([(Timestamp(0), Price(Decimal("200")))])
        
        registry.register(test_multi_output, name="multi_output_test")
        schema = registry.get("multi_output_test").schema
        assert len(schema.outputs) == 2
        assert "output_0" in schema.outputs
        assert "output_1" in schema.outputs


class TestThreadSafety:
    """Test thread safety of registry."""
    
    def test_registry_thread_safety(self) -> None:
        """Test that registry operations are thread-safe."""
        import threading
        import time
        
        registry = Registry()
        results = []
        
        def register_indicator(idx: int) -> None:
            def test_func(ctx: SeriesContext, period: int = 20) -> Series[Price]:
                return Series([(Timestamp(0), Price(Decimal("100")))])
            
            registry.register(test_func, name=f"test_{idx}")
            results.append(f"test_{idx}")
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_indicator, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all indicators were registered
        assert len(registry.list_indicators()) == 10
        assert len(results) == 10


class TestRegistryManagement:
    """Test registry management functionality."""
    
    def test_clear_registry(self) -> None:
        """Test clearing the registry."""
        registry = Registry()
        
        def test_func(ctx: SeriesContext, period: int = 20) -> Series[Price]:
            return Series([(Timestamp(0), Price(Decimal("100")))])
        
        registry.register(test_func, name="clear_test")
        
        assert len(registry.list_indicators()) == 1
        
        registry.clear()
        assert len(registry.list_indicators()) == 0
    
    def test_get_global_registry(self) -> None:
        """Test getting the global registry instance."""
        global_registry = get_global_registry()
        assert isinstance(global_registry, Registry)
        assert global_registry is get_global_registry()  # Should be the same instance
