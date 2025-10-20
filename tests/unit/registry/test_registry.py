"""Consolidated registry tests - lean and efficient."""

import pytest
from typing import Any, Union, Optional, List, Dict, Tuple
from unittest.mock import Mock
from datetime import datetime, timezone

from laakhay.ta.registry.registry import Registry, register, indicator, describe_indicator, list_indicators, list_all_names, get_global_registry
from laakhay.ta.registry.models import SeriesContext, IndicatorHandle
from laakhay.ta.registry.schemas import ParamSchema, OutputSchema, IndicatorSchema
from laakhay.ta.core.series import Series
from laakhay.ta.core.types import Price


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
    
    def test_validate_function_no_parameters(self, registry):
        """Test Registry validate function with no parameters."""
        def no_params_func() -> Series[Price]:
            return Series((), (), "TEST", "1s")
        
        with pytest.raises(ValueError, match="must have at least one parameter"):
            registry.register(no_params_func)
    
    def test_validate_function_wrong_first_parameter(self, registry):
        """Test Registry validate function with wrong first parameter."""
        def wrong_first_param_func(param: int) -> Series[Price]:
            return Series((), (), "TEST", "1s")
        
        with pytest.raises(ValueError, match="first parameter must be SeriesContext"):
            registry.register(wrong_first_param_func)
    
    def test_validate_function_wrong_return_type(self, registry):
        """Test Registry validate function with wrong return type."""
        def wrong_return_func(ctx: SeriesContext) -> str:
            return "invalid"
        
        with pytest.raises(ValueError, match="must return Series"):
            registry.register(wrong_return_func)
    
    def test_validate_function_no_return_annotation(self, registry):
        """Test Registry validate function with no return annotation."""
        def no_return_annotation_func(ctx: SeriesContext):
            return Series((), (), "TEST", "1s")
        
        registry.register(no_return_annotation_func)
        assert "no_return_annotation_func" in registry._indicators


class TestRegistryTypeHandling:
    """Registry type handling functionality."""
    
    def test_get_param_type_basic_types(self, registry):
        """Test _get_param_type with basic types."""
        assert registry._get_param_type(int) == int
        assert registry._get_param_type(float) == float
        assert registry._get_param_type(str) == str
        assert registry._get_param_type(bool) == bool
        assert registry._get_param_type(list) == list
        assert registry._get_param_type(dict) == dict
    
    def test_get_param_type_union_types(self, registry):
        """Test _get_param_type with Union types."""
        union_type = Union[int, str]
        result = registry._get_param_type(union_type)
        assert result == int  # Union types return the first type
    
    def test_get_param_type_optional_types(self, registry):
        """Test _get_param_type with Optional types."""
        optional_type = Optional[int]
        result = registry._get_param_type(optional_type)
        assert result == int  # Should return the non-None type
    
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
        def mock_function(ctx: SeriesContext) -> Tuple[Series[Price], Series[Price]]:
            return Series((), (), "TEST", "1s"), Series((), (), "TEST", "1s")
        
        mock_annotation = Tuple[Series[Price], Series[Price]]
        result = registry._build_output_schema(mock_annotation)
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"].type == Series
    
    def test_build_output_schema_dict_type(self, registry):
        """Test _build_output_schema with dict return type."""
        mock_annotation = Mock()
        mock_annotation.__origin__ = dict
        mock_annotation.__args__ = (str, Series[Price])
        result = registry._build_output_schema(mock_annotation)
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"].type == Series
    
    def test_build_output_schema_unknown_type(self, registry):
        """Test _build_output_schema with unknown return type."""
        mock_annotation = Mock()
        mock_annotation.__origin__ = None
        mock_annotation.__args__ = None
        result = registry._build_output_schema(mock_annotation)
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"].type == Series
    
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
        def complex_function(ctx: SeriesContext, 
                           param1: List[int], 
                           param2: Dict[str, float],
                           param3: Optional[Series[Price]] = None) -> Dict[str, Series[Price]]:
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
        def union_function(ctx: SeriesContext, param: Union[int, float]) -> Series[Price]:
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
        
        timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
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
