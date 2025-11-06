"""Tests for indicator schema classes."""

import pytest

from laakhay.ta.registry import (
    IndicatorMetadata,
    IndicatorSchema,
    OutputSchema,
    ParamSchema,
)


class TestParamSchema:
    """Test ParamSchema functionality."""

    def test_required_parameter(self) -> None:
        """Test required parameter creation."""
        param = ParamSchema(
            name="period", type=int, required=True, description="Period length"
        )

        assert param.name == "period"
        assert param.type == int
        assert param.required is True
        assert param.default is None
        assert param.description == "Period length"

    def test_optional_parameter(self) -> None:
        """Test optional parameter with default value."""
        param = ParamSchema(
            name="source",
            type=str,
            default="binance",
            required=False,
            description="Data source",
        )

        assert param.name == "source"
        assert param.type == str
        assert param.required is False
        assert param.default == "binance"
        assert param.description == "Data source"

    def test_parameter_with_valid_values(self) -> None:
        """Test parameter with valid value constraints."""
        param = ParamSchema(
            name="method",
            type=str,
            default="sma",
            required=False,
            description="Calculation method",
            valid_values=["sma", "ema", "wma"],
        )

        assert param.valid_values == ["sma", "ema", "wma"]

    def test_parameter_validation_errors(self) -> None:
        """Test parameter validation rules."""
        # Required parameter with default should fail
        with pytest.raises(
            ValueError, match="Required parameters cannot have default values"
        ):
            ParamSchema(name="period", type=int, required=True, default=20)

        # Optional parameter without default should now be allowed (None is valid default)
        # This should not raise an error anymore
        param = ParamSchema(name="source", type=str, required=False)
        assert param.default is None

        # Empty name should fail
        with pytest.raises(
            ValueError, match="Parameter name must be a non-empty string"
        ):
            ParamSchema(name="", type=int)

        # None name should fail
        with pytest.raises(
            ValueError, match="Parameter name must be a non-empty string"
        ):
            ParamSchema(name=None, type=int)  # type: ignore[arg-type]

        # Default value not in valid_values should fail
        with pytest.raises(ValueError, match="Default value 99 not in valid_values"):
            ParamSchema(
                name="period",
                type=int,
                default=99,
                required=False,
                valid_values=[5, 10, 20],
            )


class TestOutputSchema:
    """Test OutputSchema functionality."""

    def test_output_schema_creation(self) -> None:
        """Test basic output schema creation."""
        output = OutputSchema(name="macd", type=float, description="MACD line values")

        assert output.name == "macd"
        assert output.type == float
        assert output.description == "MACD line values"

    def test_output_schema_minimal(self) -> None:
        """Test output schema with minimal fields."""
        output = OutputSchema(name="signal", type=bool)

        assert output.name == "signal"
        assert output.type == bool
        assert output.description == ""

    def test_output_schema_validation_errors(self) -> None:
        """Test output schema validation rules."""
        # Empty name should fail
        with pytest.raises(ValueError, match="Output name must be a non-empty string"):
            OutputSchema(name="", type=float)

        # None name should fail
        with pytest.raises(ValueError, match="Output name must be a non-empty string"):
            OutputSchema(name=None, type=float)  # type: ignore[arg-type]


class TestIndicatorSchema:
    """Test IndicatorSchema functionality."""

    def test_indicator_schema_creation(self) -> None:
        """Test basic indicator schema creation."""
        param = ParamSchema(
            name="period", type=int, required=True, description="Period length"
        )
        output = OutputSchema(name="sma", type=float, description="SMA values")

        schema = IndicatorSchema(
            name="sma",
            description="Simple Moving Average",
            parameters={"period": param},
            outputs={"sma": output},
            aliases=["simple_ma", "moving_average"],
        )

        assert schema.name == "sma"
        assert schema.description == "Simple Moving Average"
        assert len(schema.parameters) == 1
        assert len(schema.outputs) == 1
        assert schema.aliases == ["simple_ma", "moving_average"]
        assert isinstance(schema.metadata, IndicatorMetadata)

    def test_indicator_schema_minimal(self) -> None:
        """Test indicator schema with minimal fields."""
        schema = IndicatorSchema(name="rsi")

        assert schema.name == "rsi"
        assert schema.description == ""
        assert len(schema.parameters) == 0
        assert len(schema.outputs) == 0
        assert len(schema.aliases) == 0

    def test_indicator_schema_to_dict(self) -> None:
        """Test schema serialization to dictionary."""
        param = ParamSchema(
            name="period", type=int, required=True, description="Period length"
        )
        output = OutputSchema(name="rsi", type=float, description="RSI values")

        schema = IndicatorSchema(
            name="rsi",
            description="Relative Strength Index",
            parameters={"period": param},
            outputs={"rsi": output},
            output_metadata={"rsi": {"type": "price", "role": "oscillator"}},
        )

        result = schema.to_dict()

        assert result["name"] == "rsi"
        assert result["description"] == "Relative Strength Index"
        assert "period" in result["parameters"]
        assert result["parameters"]["period"]["type"] == "int"
        assert result["parameters"]["period"]["required"] is True
        assert "rsi" in result["outputs"]
        assert result["outputs"]["rsi"]["type"] == "float"
        assert "metadata" in result
        assert result["metadata"]["required_fields"] == []
        assert result["output_metadata"]["rsi"]["role"] == "oscillator"

    def test_indicator_schema_from_dict(self) -> None:
        """Test schema deserialization from dictionary."""
        data = {
            "name": "sma",
            "description": "Simple Moving Average",
            "parameters": {
                "period": {
                    "type": "int",
                    "required": True,
                    "description": "Period length",
                }
            },
            "outputs": {"sma": {"type": "float", "description": "SMA values"}},
            "aliases": ["simple_ma"],
            "metadata": {
                "required_fields": [],
                "optional_fields": [],
                "lookback_params": [],
                "default_lookback": None,
            },
            "output_metadata": {"sma": {"type": "price", "role": "level"}},
        }

        schema = IndicatorSchema.from_dict(data)

        assert schema.name == "sma"
        assert schema.description == "Simple Moving Average"
        assert len(schema.parameters) == 1
        assert "period" in schema.parameters
        assert schema.parameters["period"].type == int
        assert len(schema.outputs) == 1
        assert "sma" in schema.outputs
        assert schema.outputs["sma"].type == float
        assert schema.aliases == ["simple_ma"]
        assert isinstance(schema.metadata, IndicatorMetadata)
        assert schema.output_metadata["sma"]["role"] == "level"

    def test_indicator_schema_round_trip(self) -> None:
        """Test schema serialization round-trip."""
        param = ParamSchema(
            name="fast",
            type=int,
            default=12,
            required=False,
            description="Fast period",
            valid_values=[5, 12, 26],
        )
        output = OutputSchema(name="macd", type=float, description="MACD line")

        original = IndicatorSchema(
            name="macd",
            description="MACD indicator",
            parameters={"fast": param},
            outputs={"macd": output},
            aliases=["macd_line"],
            output_metadata={"macd": {"type": "float", "role": "line"}},
        )

        # Round-trip through dict
        data = original.to_dict()
        restored = IndicatorSchema.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert len(restored.parameters) == len(original.parameters)
        assert len(restored.outputs) == len(original.outputs)
        assert restored.aliases == original.aliases
        assert isinstance(restored.metadata, IndicatorMetadata)
        assert restored.output_metadata == {"macd": {"type": "float", "role": "line"}}

    def test_indicator_schema_from_dict_validation_errors(self) -> None:
        """Test schema deserialization validation errors."""
        # Unknown parameter type should fail
        data_with_unknown_param = {
            "name": "test",
            "parameters": {
                "param": {
                    "type": "unknown_type",
                    "required": True,
                    "description": "Test param",
                }
            },
        }
        with pytest.raises(
            ValueError, match="Unsupported parameter type: unknown_type"
        ):
            IndicatorSchema.from_dict(data_with_unknown_param)

        # Unknown output type should fail
        data_with_unknown_output = {
            "name": "test",
            "outputs": {
                "output": {"type": "unknown_type", "description": "Test output"}
            },
        }
        with pytest.raises(ValueError, match="Unsupported output type: unknown_type"):
            IndicatorSchema.from_dict(data_with_unknown_output)


class TestRegistryCriticalIssues:
    """Test critical issues with the registry system identified in the audit."""

    def test_indicator_overrides_handles_any_type(self):
        """Test that indicator overrides handle Any type without isinstance error."""
        from inspect import signature
        from typing import Any

        from laakhay.ta.core.series import Series
        from laakhay.ta.core.types import Price
        from laakhay.ta.registry.models import IndicatorHandle

        def test_indicator(series: Series[Price], param: Any) -> Series[Price]:
            """Test indicator with unannotated param."""
            return series

        # This should work but may fail due to isinstance(Any) issue
        schema = IndicatorSchema(
            name="test",
            description="Test indicator",
            parameters={
                "param": ParamSchema(
                    name="param",
                    type=Any,  # This causes the isinstance issue
                    required=True,
                    description="Test param",
                )
            },
        )

        handle = IndicatorHandle(
            name="test",
            func=test_indicator,
            signature=signature(test_indicator),
            schema=schema,
            aliases=[],
        )

        # This should not raise TypeError
        try:
            result = handle.with_overrides(param="test_value")
            assert result is not None
        except TypeError as e:
            if "typing.Any cannot be used with isinstance()" in str(e):
                pytest.fail("Registry should handle Any type without isinstance error")
            else:
                raise

    def test_optional_parameters_work_correctly(self):
        """Test that optional parameters work correctly."""
        from inspect import signature
        from typing import Optional

        from laakhay.ta.core.series import Series
        from laakhay.ta.core.types import Price
        from laakhay.ta.registry.models import IndicatorHandle

        def test_indicator(
            series: Series[Price], optional_param: int | None = None
        ) -> Series[Price]:
            """Test indicator with optional parameter."""
            return series

        # This should work - optional params should be optional
        schema = IndicatorSchema(
            name="test",
            description="Test indicator",
            parameters={
                "optional_param": ParamSchema(
                    name="optional_param",
                    type=Optional[int],
                    required=False,  # Should be False for optional params
                    default=None,  # Add default for optional param
                    description="Optional param",
                )
            },
        )

        handle = IndicatorHandle(
            name="test",
            func=test_indicator,
            signature=signature(test_indicator),
            schema=schema,
            aliases=[],
        )

        # This should work without providing the optional parameter
        result = handle.with_overrides()
        assert result is not None
