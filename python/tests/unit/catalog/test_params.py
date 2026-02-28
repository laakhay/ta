"""Tests for parameter coercion functionality."""

import pytest

from laakhay.ta.catalog.params import (
    ParameterCoercionError,
    ParameterParser,
    coerce_parameter,
    coerce_parameters,
)


class TestParameterParser:
    """Test ParameterParser class."""

    def test_coerce_int(self):
        """Test coercing int parameter."""
        parser = ParameterParser()
        spec = {"name": "period", "param_type": "int", "required": True, "default_value": None}
        result = parser.coerce_value(spec, "20")
        assert isinstance(result, int)
        assert result == 20

    def test_coerce_float(self):
        """Test coercing float parameter."""
        parser = ParameterParser()
        spec = {"name": "threshold", "param_type": "float", "required": False, "default_value": 0.5}
        result = parser.coerce_value(spec, "1.5")
        assert isinstance(result, float)
        assert result == 1.5

    def test_coerce_string(self):
        """Test coercing string parameter."""
        parser = ParameterParser()
        spec = {"name": "field", "param_type": "string", "required": False, "default_value": "close"}
        result = parser.coerce_value(spec, "high")
        assert isinstance(result, str)
        assert result == "high"

    def test_coerce_bool(self):
        """Test coercing bool parameter."""
        parser = ParameterParser()
        spec = {"name": "enabled", "param_type": "bool", "required": False, "default_value": False}

        # Test various boolean string formats
        assert parser.coerce_value(spec, "true") is True
        assert parser.coerce_value(spec, "1") is True
        assert parser.coerce_value(spec, "yes") is True
        assert parser.coerce_value(spec, "false") is False
        assert parser.coerce_value(spec, "0") is False
        assert parser.coerce_value(spec, "no") is False
        assert parser.coerce_value(spec, True) is True
        assert parser.coerce_value(spec, False) is False

    def test_coerce_enum(self):
        """Test coercing enum parameter."""
        parser = ParameterParser()
        spec = {
            "name": "mode",
            "param_type": "enum",
            "required": False,
            "default_value": "fast",
            "options": ["fast", "slow"],
        }
        result = parser.coerce_value(spec, "slow")
        assert result == "slow"

    def test_coerce_enum_invalid(self):
        """Test coercing invalid enum value raises error."""
        parser = ParameterParser()
        spec = {
            "name": "mode",
            "param_type": "enum",
            "required": False,
            "default_value": "fast",
            "options": ["fast", "slow"],
        }
        with pytest.raises(ParameterCoercionError) as exc_info:
            parser.coerce_value(spec, "invalid")
        # Error message should mention the parameter or the options
        assert "mode" in str(exc_info.value) or "fast" in str(exc_info.value)

    def test_coerce_required_missing(self):
        """Test that required parameters raise error when missing."""
        parser = ParameterParser()
        spec = {"name": "period", "param_type": "int", "required": True, "default_value": None}
        with pytest.raises(ParameterCoercionError, match="required"):
            parser.coerce_value(spec, None)

    def test_coerce_default_value(self):
        """Test that default values are used when value is None."""
        parser = ParameterParser()
        spec = {"name": "period", "param_type": "int", "required": False, "default_value": 20}
        result = parser.coerce_value(spec, None)
        assert result == 20

    def test_coerce_list(self):
        """Test coercing list parameter."""
        parser = ParameterParser()
        spec = {
            "name": "values",
            "param_type": "json",
            "required": False,
            "collection": True,
            "collection_python_type": list,
            "item_type": "int",
            "default_value": None,
        }
        result = parser.coerce_value(spec, "[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_coerce_parameters_multiple(self):
        """Test coercing multiple parameters."""
        parser = ParameterParser()
        specs = {
            "period": {"name": "period", "param_type": "int", "required": True, "default_value": None},
            "threshold": {"name": "threshold", "param_type": "float", "required": False, "default_value": 0.5},
        }
        raw = {"period": "20", "threshold": "1.5"}
        result = parser.coerce_parameters(specs, raw)
        assert result["period"] == 20
        assert result["threshold"] == 1.5

    def test_coerce_parameters_unknown(self):
        """Test that unknown parameters raise error."""
        parser = ParameterParser()
        specs = {"period": {"name": "period", "param_type": "int", "required": True, "default_value": None}}
        raw = {"period": "20", "unknown": "value"}
        with pytest.raises(ParameterCoercionError, match="Unexpected parameters"):
            parser.coerce_parameters(specs, raw)


class TestCoerceParameterConvenience:
    """Test convenience functions."""

    def test_coerce_parameter_int(self):
        """Test convenience function for single parameter."""
        result = coerce_parameter("int", "20")
        assert result == 20

    def test_coerce_parameter_enum(self):
        """Test convenience function with enum."""
        result = coerce_parameter("enum", "fast", options=["fast", "slow"])
        assert result == "fast"

    def test_coerce_parameters_multiple(self):
        """Test convenience function for multiple parameters."""
        specs = {
            "period": {"name": "period", "param_type": "int", "required": True, "default_value": None},
            "threshold": {"name": "threshold", "param_type": "float", "required": False, "default_value": 0.5},
        }
        raw = {"period": "20", "threshold": "1.5"}
        result = coerce_parameters(specs, raw)
        assert result["period"] == 20
        assert result["threshold"] == 1.5
