"""Tests for indicator schema classes."""

import pytest

from laakhay.ta.registry import (
    ConstraintSpec,
    IndicatorSchema,
    IndicatorSpec,
    InputSlotSpec,
    OutputSchema,
    OutputSpec,
    ParamSchema,
    ParamSpec,
    RuntimeBindingSpec,
    SemanticsSpec,
    indicator_spec_to_schema,
    schema_to_indicator_spec,
)


class TestParamSchema:
    """Test ParamSchema functionality."""

    def test_required_parameter(self) -> None:
        """Test required parameter creation."""
        param = ParamSchema(name="period", type=int, required=True, description="Period length")

        assert param.name == "period"
        assert param.type is int
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
        assert param.type is str
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
        with pytest.raises(ValueError, match="Required parameters cannot have default values"):
            ParamSchema(name="period", type=int, required=True, default=20)

        # Optional parameter without default should now be allowed (None is valid default)
        # This should not raise an error anymore
        param = ParamSchema(name="source", type=str, required=False)
        assert param.default is None

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
                valid_values=[5, 10, 20],
            )


class TestOutputSchema:
    """Test OutputSchema functionality."""

    def test_output_schema_creation(self) -> None:
        """Test basic output schema creation."""
        output = OutputSchema(name="macd", type=float, description="MACD line values")

        assert output.name == "macd"
        assert output.type is float
        assert output.description == "MACD line values"

    def test_output_schema_minimal(self) -> None:
        """Test output schema with minimal fields."""
        output = OutputSchema(name="signal", type=bool)

        assert output.name == "signal"
        assert output.type is bool
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
            aliases=["simple_ma", "moving_average"],
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
        param = ParamSchema(name="period", type=int, required=True, description="Period length")
        output = OutputSchema(name="rsi", type=float, description="RSI values")

        schema = IndicatorSchema(
            name="rsi",
            description="Relative Strength Index",
            parameters={"period": param},
            outputs={"rsi": output},
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
                    "description": "Period length",
                }
            },
            "outputs": {"sma": {"type": "float", "description": "SMA values"}},
            "aliases": ["simple_ma"],
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
            valid_values=[5, 12, 26],
        )
        output = OutputSchema(name="macd", type=float, description="MACD line")

        original = IndicatorSchema(
            name="macd",
            description="MACD indicator",
            parameters={"fast": param},
            outputs={"macd": output},
            aliases=["macd_line"],
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
                    "description": "Test param",
                }
            },
        }
        with pytest.raises(ValueError, match="Unsupported parameter type: unknown_type"):
            IndicatorSchema.from_dict(data_with_unknown_param)

        # Unknown output type should fail
        data_with_unknown_output = {
            "name": "test",
            "outputs": {"output": {"type": "unknown_type", "description": "Test output"}},
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
            indicator_spec=schema_to_indicator_spec(schema),
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

        from laakhay.ta.core.series import Series
        from laakhay.ta.core.types import Price
        from laakhay.ta.registry.models import IndicatorHandle

        def test_indicator(series: Series[Price], optional_param: int | None = None) -> Series[Price]:
            """Test indicator with optional parameter."""
            return series

        # This should work - optional params should be optional
        schema = IndicatorSchema(
            name="test",
            description="Test indicator",
            parameters={
                "optional_param": ParamSchema(
                    name="optional_param",
                    type=int | None,
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
            indicator_spec=schema_to_indicator_spec(schema),
            aliases=[],
        )

        # This should work without providing the optional parameter
        result = handle.with_overrides()
        assert result is not None


class TestIndicatorSpecModels:
    """Tests for strict IndicatorSpec models (Phase 1.1)."""

    def test_input_slot_spec(self) -> None:
        slot = InputSlotSpec(
            name="input_series",
            description="Override input series",
            required=False,
            default_source="ohlcv",
            default_field="close",
        )
        assert slot.name == "input_series"
        assert slot.default_field == "close"

    def test_param_spec_with_min_max(self) -> None:
        param = ParamSpec(
            name="period",
            type=int,
            default=14,
            required=False,
            min_value=1,
            max_value=500,
        )
        assert param.min_value == 1
        assert param.max_value == 500

    def test_output_spec_with_role_polarity(self) -> None:
        out = OutputSpec(
            name="swing_high",
            type=float,
            role="level",
            polarity="high",
        )
        assert out.role == "level"
        assert out.polarity == "high"

    def test_semantics_spec(self) -> None:
        sem = SemanticsSpec(
            required_fields=("close",),
            lookback_params=("period",),
            default_lookback=14,
            input_field="close",
            input_series_param="input_series",
        )
        assert sem.required_fields == ("close",)
        assert sem.input_field == "close"

    def test_runtime_binding_spec(self) -> None:
        binding = RuntimeBindingSpec(kernel_id="sma")
        assert binding.kernel_id == "sma"

    def test_constraint_spec(self) -> None:
        constraint = ConstraintSpec(
            param_names=("fast", "slow"),
            constraint_type="less_than",
            extra={"message": "fast must be less than slow"},
        )
        assert constraint.param_names == ("fast", "slow")
        assert constraint.constraint_type == "less_than"

    def test_indicator_spec_full(self) -> None:
        spec = IndicatorSpec(
            name="rsi",
            description="RSI indicator",
            inputs=(
                InputSlotSpec(
                    name="input_series",
                    default_field="close",
                ),
            ),
            params={
                "period": ParamSpec(name="period", type=int, default=14, required=False),
            },
            outputs={
                "rsi": OutputSpec(
                    name="rsi",
                    type=float,
                    role="oscillator",
                ),
            },
            semantics=SemanticsSpec(
                required_fields=("close",),
                lookback_params=("period",),
            ),
            runtime_binding=RuntimeBindingSpec(kernel_id="rsi"),
            aliases=("rsi_14",),
            param_aliases={"lookback": "period"},
        )
        assert spec.name == "rsi"
        assert len(spec.inputs) == 1
        assert "period" in spec.params
        assert "rsi" in spec.outputs
        assert spec.semantics.required_fields == ("close",)

    def test_indicator_spec_empty_name_fails(self) -> None:
        with pytest.raises(ValueError, match="Indicator name must be a non-empty string"):
            IndicatorSpec(name="")


class TestIndicatorSpecConversion:
    """Tests for indicator_spec_to_schema and schema_to_indicator_spec."""

    def test_indicator_spec_to_schema(self) -> None:
        spec = IndicatorSpec(
            name="sma",
            description="SMA",
            params={"period": ParamSpec(name="period", type=int, required=True)},
            outputs={"result": OutputSpec(name="result", type=float, role="line")},
            semantics=SemanticsSpec(
                required_fields=("close",),
                lookback_params=("period",),
                input_field="close",
                input_series_param="input_series",
            ),
            runtime_binding=RuntimeBindingSpec(kernel_id="sma"),
            aliases=("simple_ma",),
            param_aliases={"lookback": "period"},
        )
        schema = indicator_spec_to_schema(spec)

        assert schema.name == "sma"
        assert "period" in schema.parameters
        assert schema.parameters["period"].type == int
        assert "result" in schema.outputs
        assert schema.aliases == ["simple_ma"]
        assert schema.parameter_aliases == {"lookback": "period"}

    def test_schema_to_indicator_spec(self) -> None:
        schema = IndicatorSchema(
            name="rsi",
            description="RSI",
            parameters={
                "period": ParamSchema(name="period", type=int, default=14, required=False),
            },
            outputs={"rsi": OutputSchema(name="rsi", type=float, description="RSI values")},
            aliases=["rsi_14"],
            parameter_aliases={"lookback": "period"},
        )
        spec = schema_to_indicator_spec(schema)

        assert spec.name == "rsi"
        assert spec.params["period"].type == int
        assert spec.outputs["rsi"].role == "line"
        assert spec.semantics.required_fields == ()
        assert spec.runtime_binding.kernel_id == "rsi"
        assert "rsi_14" in spec.aliases
        assert spec.param_aliases["lookback"] == "period"

    def test_schema_to_indicator_spec_preserves_polarity(self) -> None:
        schema = IndicatorSchema(
            name="swing",
            outputs={"swing_high": OutputSchema(name="swing_high", type=float)},
        )
        spec = schema_to_indicator_spec(schema)
        assert spec.outputs["swing_high"].polarity is None
        assert spec.outputs["swing_high"].role == "line"

    def test_spec_to_schema_round_trip(self) -> None:
        """Round-trip: spec -> schema -> spec preserves key fields."""
        orig = IndicatorSpec(
            name="macd",
            description="MACD",
            params={
                "fast": ParamSpec(name="fast", type=int, default=12, required=False),
                "slow": ParamSpec(name="slow", type=int, default=26, required=False),
            },
            outputs={
                "macd": OutputSpec(name="macd", type=float, role="line"),
                "signal": OutputSpec(name="signal", type=float, role="signal"),
                "histogram": OutputSpec(name="histogram", type=float, role="histogram"),
            },
            semantics=SemanticsSpec(
                required_fields=("close",),
                lookback_params=("fast_period", "slow_period"),
            ),
            runtime_binding=RuntimeBindingSpec(kernel_id="macd"),
        )
        schema = indicator_spec_to_schema(orig)
        back = schema_to_indicator_spec(schema)

        assert back.name == orig.name
        assert set(back.params.keys()) == set(orig.params.keys())
        assert set(back.outputs.keys()) == set(orig.outputs.keys())
        assert back.semantics.required_fields == ()
        assert back.outputs["macd"].role == "line"
        assert back.outputs["histogram"].role == "line"
