"""Tests for indicator schema classes."""

import pytest

from laakhay.ta.registry import ParamSchema, OutputSchema, IndicatorSchema


class TestParamSchema:
    """Test ParamSchema functionality."""

    def test_required_parameter(self) -> None:
        """Test required parameter creation."""
        param = ParamSchema(
            name="period",
            type=int,
            required=True,
            description="Period length"
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
            description="Data source"
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
            valid_values=["sma", "ema", "wma"]
        )
        
        assert param.valid_values == ["sma", "ema", "wma"]

    def test_parameter_validation_errors(self) -> None:
        """Test parameter validation rules."""
        # Required parameter with default should fail
        with pytest.raises(ValueError, match="Required parameters cannot have default values"):
            ParamSchema(name="period", type=int, required=True, default=20)
        
        # Optional parameter without default should fail
        with pytest.raises(ValueError, match="Optional parameters must have default values"):
            ParamSchema(name="source", type=str, required=False)
        
        # Empty name should fail
        with pytest.raises(ValueError, match="Parameter name must be a non-empty string"):
            ParamSchema(name="", type=int)
        
        # None name should fail
        with pytest.raises(ValueError, match="Parameter name must be a non-empty string"):
            ParamSchema(name=None, type=int)  # type: ignore[arg-type]
        
        # Default value not in valid_values should fail
        with pytest.raises(ValueError, match="Default value 99 not in valid_values"):
            ParamSchema(
                name="period", 
                type=int, 
                default=99, 
                required=False,
                valid_values=[5, 10, 20]
            )


class TestOutputSchema:
    """Test OutputSchema functionality."""

    def test_output_schema_creation(self) -> None:
        """Test basic output schema creation."""
        output = OutputSchema(
            name="macd",
            type=float,
            description="MACD line values"
        )
        
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
        param = ParamSchema(name="period", type=int, required=True, description="Period length")
        output = OutputSchema(name="sma", type=float, description="SMA values")
        
        schema = IndicatorSchema(
            name="sma",
            description="Simple Moving Average",
            parameters={"period": param},
            outputs={"sma": output},
            aliases=["simple_ma", "moving_average"]
        )
        
        assert schema.name == "sma"
        assert schema.description == "Simple Moving Average"
        assert len(schema.parameters) == 1
        assert len(schema.outputs) == 1
        assert schema.aliases == ["simple_ma", "moving_average"]

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
            name="period",
            type=int,
            required=True,
            description="Period length"
        )
        output = OutputSchema(name="rsi", type=float, description="RSI values")
        
        schema = IndicatorSchema(
            name="rsi",
            description="Relative Strength Index",
            parameters={"period": param},
            outputs={"rsi": output}
        )
        
        result = schema.to_dict()
        
        assert result["name"] == "rsi"
        assert result["description"] == "Relative Strength Index"
        assert "period" in result["parameters"]
        assert result["parameters"]["period"]["type"] == "int"
        assert result["parameters"]["period"]["required"] is True
        assert "rsi" in result["outputs"]
        assert result["outputs"]["rsi"]["type"] == "float"

    def test_indicator_schema_from_dict(self) -> None:
        """Test schema deserialization from dictionary."""
        data = {
            "name": "sma",
            "description": "Simple Moving Average",
            "parameters": {
                "period": {
                    "type": "int",
                    "required": True,
                    "description": "Period length"
                }
            },
            "outputs": {
                "sma": {
                    "type": "float",
                    "description": "SMA values"
                }
            },
            "aliases": ["simple_ma"]
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

    def test_indicator_schema_round_trip(self) -> None:
        """Test schema serialization round-trip."""
        param = ParamSchema(
            name="fast",
            type=int,
            default=12,
            required=False,
            description="Fast period",
            valid_values=[5, 12, 26]
        )
        output = OutputSchema(name="macd", type=float, description="MACD line")
        
        original = IndicatorSchema(
            name="macd",
            description="MACD indicator",
            parameters={"fast": param},
            outputs={"macd": output},
            aliases=["macd_line"]
        )
        
        # Round-trip through dict
        data = original.to_dict()
        restored = IndicatorSchema.from_dict(data)
        
        assert restored.name == original.name
        assert restored.description == original.description
        assert len(restored.parameters) == len(original.parameters)
        assert len(restored.outputs) == len(original.outputs)
        assert restored.aliases == original.aliases

    def test_indicator_schema_from_dict_validation_errors(self) -> None:
        """Test schema deserialization validation errors."""
        # Unknown parameter type should fail
        data_with_unknown_param = {
            "name": "test",
            "parameters": {
                "param": {
                    "type": "unknown_type",
                    "required": True,
                    "description": "Test param"
                }
            }
        }
        with pytest.raises(ValueError, match="Unsupported parameter type: unknown_type"):
            IndicatorSchema.from_dict(data_with_unknown_param)
        
        # Unknown output type should fail
        data_with_unknown_output = {
            "name": "test",
            "outputs": {
                "output": {
                    "type": "unknown_type",
                    "description": "Test output"
                }
            }
        }
        with pytest.raises(ValueError, match="Unsupported output type: unknown_type"):
            IndicatorSchema.from_dict(data_with_unknown_output)
