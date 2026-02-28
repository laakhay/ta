"""Consolidated registry tests - lean and efficient."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock

import pytest

from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price
from laakhay.ta.registry.models import SeriesContext
from laakhay.ta.registry.registry import (
    describe_indicator,
    get_global_registry,
    indicator,
    list_all_names,
    list_indicators,
    register,
)


class TestSeriesContext:
    """SeriesContext functionality."""

    def test_initialization_and_access(self, test_series):
        """Test SeriesContext initialization and series access."""
        context = SeriesContext(price_series=test_series)
        assert context.price_series == test_series

        available = context.available_series
        assert "price_series" in available
        assert len(available) == 1

    def test_private_attribute_access(self, test_series):
        """Test SeriesContext private attribute access raises error."""
        context = SeriesContext(test_series=test_series)
        with pytest.raises(AttributeError, match="'SeriesContext' object has no attribute '_private'"):
            _ = context._private

    def test_missing_series_access(self, test_series):
        """Test SeriesContext missing series access raises error."""
        context = SeriesContext(test_series=test_series)
        with pytest.raises(AttributeError, match="Series 'missing_series' not found in context"):
            _ = context.missing_series


class TestIndicatorHandle:
    """IndicatorHandle functionality."""

    def test_call(self, indicator_handle, series_context):
        """Test IndicatorHandle call functionality."""
        result = indicator_handle(series_context, test_param=42.0)
        assert isinstance(result, Series)

    def test_parameter_coercion_int_to_float(self, indicator_handle):
        """Test parameter coercion from int to float."""
        result_handle = indicator_handle.with_overrides(test_param=42)
        assert result_handle is not None

    def test_parameter_coercion_str_to_float(self, indicator_handle):
        """Test parameter coercion from string to float."""
        result_handle = indicator_handle.with_overrides(test_param="42.5")
        assert result_handle is not None

    def test_parameter_coercion_str_to_float_invalid(self, indicator_handle):
        """Test parameter coercion from invalid string to float raises error."""
        with pytest.raises(ValueError, match="Parameter 'test_param' expects float, got str"):
            indicator_handle.with_overrides(test_param="invalid")

    def test_parameter_coercion_wrong_type(self, indicator_handle):
        """Test parameter coercion with wrong type raises error."""
        with pytest.raises(ValueError, match="Parameter 'test_param' expects float, got list"):
            indicator_handle.with_overrides(test_param=[])

    def test_unknown_parameter_error(self, indicator_handle):
        """Test IndicatorHandle with unknown parameter raises error."""
        with pytest.raises(ValueError, match="Unknown parameter 'unknown_param' for indicator"):
            indicator_handle.with_overrides(unknown_param=42)

    def test_partial_function(self, indicator_handle, series_context):
        """Test IndicatorHandle partial function creation."""
        result_handle = indicator_handle.with_overrides(test_param=42.0)
        result = result_handle(series_context)
        assert isinstance(result, Series)


class TestRegistry:
    """Registry functionality."""

    def test_register_function(self, registry, test_function):
        """Test registering a function."""
        registry.register(test_function, "test_func")
        assert "test_func" in registry._indicators

    def test_get_indicator(self, registry, test_function):
        """Test getting an indicator."""
        registry.register(test_function, "test_func")
        handle = registry.get("test_func")
        assert handle is not None
        assert handle.name == "test_func"

    def test_alias_conflict_error(self, registry, test_function):
        """Test Registry alias conflict error."""

        def test_func2(ctx: SeriesContext) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        registry.register(test_function, "func1")
        with pytest.raises(ValueError, match="Alias 'func1' conflicts with existing indicator"):
            registry.register(test_func2, "func2", aliases=["func1"])

    def test_alias_resolution(self, registry, test_function):
        """Test Registry alias resolution."""
        registry.register(test_function, "original_name", aliases=["alias_name"])
        handle = registry.get("alias_name")
        assert handle is not None
        assert handle.name == "original_name"

    def test_get_nonexistent_indicator(self, registry):
        """Test Registry get nonexistent indicator."""
        handle = registry.get("nonexistent")
        assert handle is None

    def test_list_indicators(self, registry, test_function):
        """Test Registry list indicators."""
        registry.register(test_function, "func1")
        registry.register(test_function, "func2")
        indicators = registry.list_indicators()
        assert "func1" in indicators
        assert "func2" in indicators
        assert len(indicators) == 2

    def test_list_all_names(self, registry, test_function):
        """Test Registry list all names including aliases."""
        registry.register(test_function, "original_name", aliases=["alias_name"])
        all_names = registry.list_all_names()
        assert "original_name" in all_names
        assert "alias_name" in all_names
        assert len(all_names) == 2

    def test_clear(self, registry, test_function):
        """Test Registry clear functionality."""
        registry.register(test_function, "original_name", aliases=["alias_name"])
        assert len(registry.list_indicators()) == 1
        registry.clear()
        assert len(registry.list_indicators()) == 0


class TestRegistryValidation:
    """Registry validation functionality."""

    def test_validate_function_comprehensive(self, registry):
        """Test Registry comprehensive function validation."""

        # Test no parameters
        def no_params_func() -> Series[Price]:
            return Series((), (), "TEST", "1s")

        with pytest.raises(ValueError, match="must have at least one parameter"):
            registry.register(no_params_func)

        # Test wrong first parameter
        def wrong_first_param_func(param: int) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        with pytest.raises(ValueError, match="first parameter must be SeriesContext"):
            registry.register(wrong_first_param_func)

        # Test wrong return type
        def wrong_return_func(ctx: SeriesContext) -> str:
            return "invalid"

        with pytest.raises(ValueError, match="must return Series"):
            registry.register(wrong_return_func)

        # Test no return annotation (should work)
        def no_return_annotation_func(ctx: SeriesContext):
            return Series((), (), "TEST", "1s")

        registry.register(no_return_annotation_func)
        assert "no_return_annotation_func" in registry._indicators


class TestRegistryTypeHandling:
    """Registry type handling functionality."""

    def test_get_param_type_basic_types(self, registry):
        """Test _get_param_type with basic types."""
        assert registry._get_param_type(int) is int
        assert registry._get_param_type(float) is float
        assert registry._get_param_type(str) is str
        assert registry._get_param_type(bool) is bool
        assert registry._get_param_type(list) is list
        assert registry._get_param_type(dict) is dict

    def test_get_param_type_union_types(self, registry):
        """Test _get_param_type with Union types."""
        union_type = int | str
        result = registry._get_param_type(union_type)
        assert result is Any

    def test_get_param_type_optional_types(self, registry):
        """Test _get_param_type with Optional types."""
        optional_type = int | None
        result = registry._get_param_type(optional_type)
        assert result is Any

    def test_get_param_type_generic_types(self, registry):
        """Test _get_param_type with generic types."""
        mock_annotation = Mock()
        mock_annotation.__origin__ = Series
        mock_annotation.__args__ = (Price,)
        result = registry._get_param_type(mock_annotation)
        assert result == Series

    def test_get_param_type_unknown_type(self, registry):
        """Test _get_param_type with unknown type."""
        mock_annotation = Mock()
        mock_annotation.__origin__ = None
        mock_annotation.__args__ = None
        result = registry._get_param_type(mock_annotation)
        assert result == Any


class TestRegistrySchemaBuilding:
    """Registry schema building functionality."""

    def test_build_output_schema_tuple_type(self, registry):
        """Test _build_output_schema with tuple return type."""

        def mock_function(ctx: SeriesContext) -> tuple[Series[Price], Series[Price]]:
            return Series((), (), "TEST", "1s"), Series((), (), "TEST", "1s")

        mock_annotation = tuple[Series[Price], Series[Price]]
        result = registry._build_output_schema(mock_annotation)
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"].type is Series

    def test_build_output_schema_dict_type(self, registry):
        """Test _build_output_schema with dict return type."""
        mock_annotation = Mock()
        mock_annotation.__origin__ = dict
        mock_annotation.__args__ = (str, Series[Price])
        result = registry._build_output_schema(mock_annotation)
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"].type is Series

    def test_build_output_schema_unknown_type(self, registry):
        """Test _build_output_schema with unknown return type."""
        mock_annotation = Mock()
        mock_annotation.__origin__ = None
        mock_annotation.__args__ = None
        result = registry._build_output_schema(mock_annotation)
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"].type is Series

    def test_build_schema_skip_first_parameter(self, registry):
        """Test _build_schema skips first parameter (SeriesContext)."""

        def test_function(ctx: SeriesContext, param1: int, param2: str = "default") -> Series[Price]:
            return Series((), (), "TEST", "1s")

        schema = registry._build_schema(test_function, "test_function", "Test function")
        assert len(schema.parameters) == 2
        assert "param1" in schema.parameters
        assert "param2" in schema.parameters
        assert "ctx" not in schema.parameters

    def test_build_schema_required_parameter_detection(self, registry):
        """Test _build_schema correctly detects required parameters."""

        def test_function(ctx: SeriesContext, required_param: int, optional_param: str = "default") -> Series[Price]:
            return Series((), (), "TEST", "1s")

        schema = registry._build_schema(test_function, "test_function", "Test function")
        required_param = schema.parameters["required_param"]
        assert required_param.required is True
        assert required_param.default is None

        optional_param = schema.parameters["optional_param"]
        assert optional_param.required is False
        assert optional_param.default == "default"


class TestRegistryEdgeCases:
    """Registry edge cases."""

    def test_register_function_with_complex_types(self, registry):
        """Test registering function with complex type annotations."""

        def complex_function(
            ctx: SeriesContext,
            param1: list[int],
            param2: dict[str, float],
            param3: Series[Price] | None = None,
        ) -> dict[str, Series[Price]]:
            return {"result": Series((), (), "TEST", "1s")}

        registry.register(complex_function, "complex_test")
        assert "complex_test" in registry._indicators

        handle = registry.get("complex_test")
        assert handle is not None
        assert handle.name == "complex_test"

        schema = handle.schema
        assert len(schema.parameters) == 3
        assert "param1" in schema.parameters
        assert "param2" in schema.parameters
        assert "param3" in schema.parameters

    def test_register_function_with_union_types(self, registry):
        """Test registering function with Union types."""

        def union_function(ctx: SeriesContext, param: int | float) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        registry.register(union_function, "union_test")
        assert "union_test" in registry._indicators

        handle = registry.get("union_test")
        assert handle is not None
        schema = handle.schema
        assert "param" in schema.parameters
        assert schema.parameters["param"].type in [int, float, Any]


class TestRegistryGlobalFunctions:
    """Registry global functions."""

    def test_register_decorator(self):
        """Test register decorator."""

        @register("test_global_func")
        def test_global_func(ctx: SeriesContext) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        registry = get_global_registry()
        assert "test_global_func" in registry._indicators

    def test_indicator_function(self):
        """Test indicator function."""

        @register("test_indicator_func")
        def test_indicator_func(ctx: SeriesContext) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        context = SeriesContext(test_series=Series((timestamp,), (Price(100),), "TEST", "1s"))
        result = indicator("test_indicator_func")(context)
        assert isinstance(result, Series)

    def test_indicator_function_not_found(self):
        """Test indicator function not found."""
        with pytest.raises(ValueError, match="Indicator 'nonexistent' not found"):
            indicator("nonexistent")

    def test_describe_indicator_function(self):
        """Test describe indicator function."""

        @register("test_describe_func")
        def test_describe_func(ctx: SeriesContext) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        schema = describe_indicator("test_describe_func")
        assert schema is not None
        assert schema.name == "test_describe_func"

    def test_describe_indicator_not_found(self):
        """Test describe indicator not found."""
        with pytest.raises(ValueError, match="Indicator 'nonexistent' not found"):
            describe_indicator("nonexistent")

    def test_list_indicators_function(self):
        """Test list indicators function."""

        @register("test_list_func")
        def test_list_func(ctx: SeriesContext) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        indicators = list_indicators()
        assert "test_list_func" in indicators

    def test_list_all_names_function(self):
        """Test list all names function."""

        @register("test_list_all_func", aliases=["alias_func"])
        def test_list_all_func(ctx: SeriesContext) -> Series[Price]:
            return Series((), (), "TEST", "1s")

        all_names = list_all_names()
        assert "test_list_all_func" in all_names
        assert "alias_func" in all_names


class TestRegistryErrorHandling:
    """Test registry error handling and edge cases."""

    def test_register_indicator_no_annotation_warning(self):
        """Test registering indicator with no annotation on first parameter."""
        from laakhay.ta.registry import Registry

        registry = Registry()

        def test_indicator(series, period: int = 20) -> Series[Price]:
            """Test indicator with no annotation on first parameter."""
            return series

        # This should work but may trigger warnings
        registry.register(test_indicator)
        assert "test_indicator" in registry._indicators

    def test_register_indicator_wrong_first_parameter_type(self):
        """Test registering indicator with wrong first parameter type."""
        from laakhay.ta.registry import Registry

        registry = Registry()

        def test_indicator(period: int) -> Series[Price]:  # Wrong first parameter
            """Test indicator with wrong first parameter type."""
            return Series[Price](timestamps=(), values=(), symbol="TEST", timeframe="1h")

        # This should raise an error
        with pytest.raises(
            ValueError,
            match="Indicator function 'test_indicator' first parameter must be SeriesContext",
        ):
            registry.register(test_indicator)

    def test_register_indicator_no_parameters(self):
        """Test registering indicator with no parameters."""
        from laakhay.ta.registry import Registry

        registry = Registry()

        def test_indicator() -> Series[Price]:  # No parameters
            """Test indicator with no parameters."""
            return Series[Price](timestamps=(), values=(), symbol="TEST", timeframe="1h")

        # This should raise an error
        with pytest.raises(
            ValueError,
            match="Indicator function 'test_indicator' must have at least one parameter",
        ):
            registry.register(test_indicator)

    def test_register_indicator_comprehensive_return_types(self):
        """Test registering indicators with various return types."""

        from laakhay.ta.registry import Registry

        registry = Registry()

        # Test Series return type
        def series_indicator(ctx: SeriesContext) -> Series[Price]:
            return Series[Price]((), (), "TEST", "1h")

        # Test Tuple return type
        def tuple_indicator(ctx: SeriesContext) -> tuple[Series[Price], Series[Price]]:
            series = Series[Price]((), (), "TEST", "1h")
            return series, series

        # Test Dict return type
        def dict_indicator(ctx: SeriesContext) -> dict[str, Series[Price]]:
            series = Series[Price]((), (), "TEST", "1h")
            return {"output": series}

        # Test invalid return type
        def invalid_indicator(ctx: SeriesContext) -> str:
            return "invalid"

        # Register valid indicators
        registry.register(series_indicator)
        registry.register(tuple_indicator)
        registry.register(dict_indicator)

        assert "series_indicator" in registry._indicators
        assert "tuple_indicator" in registry._indicators
        assert "dict_indicator" in registry._indicators

        # Test invalid return type raises error
        with pytest.raises(
            ValueError,
            match="Indicator function 'invalid_indicator' must return Series",
        ):
            registry.register(invalid_indicator)

    def test_register_indicator_unsupported_return_types_error(self):
        """Test registering indicators with unsupported return types raises errors."""

        from laakhay.ta.registry import Registry

        registry = Registry()

        # Test Union return type
        def union_indicator(ctx: SeriesContext) -> Series[Price] | str:
            return Series[Price]((), (), "TEST", "1h")

        # Test Optional return type
        def optional_indicator(ctx: SeriesContext) -> Series[Price] | None:
            return Series[Price]((), (), "TEST", "1h")

        # Test List return type
        def list_indicator(ctx: SeriesContext) -> list[Series[Price]]:
            return [Series[Price]((), (), "TEST", "1h")]

        # Test int return type
        def int_indicator(ctx: SeriesContext) -> int:
            return 42

        # Test all unsupported types raise errors
        with pytest.raises(ValueError, match="Indicator function 'union_indicator' must return Series"):
            registry.register(union_indicator)

        with pytest.raises(
            ValueError,
            match="Indicator function 'optional_indicator' must return Series",
        ):
            registry.register(optional_indicator)

        with pytest.raises(ValueError, match="Indicator function 'list_indicator' must return Series"):
            registry.register(list_indicator)

        with pytest.raises(ValueError, match="Indicator function 'int_indicator' must return Series"):
            registry.register(int_indicator)
