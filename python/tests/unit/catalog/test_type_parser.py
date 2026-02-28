"""Tests for type parser functionality."""

from typing import Literal

from laakhay.ta.catalog.type_parser import TypeParser, classify_parameter_type
from laakhay.ta.core import Series
from laakhay.ta.core.types import Price


class TestTypeParser:
    """Test TypeParser class."""

    def test_classify_int(self):
        """Test classifying int parameter."""
        parser = TypeParser()
        import inspect

        # When default is inspect.Parameter.empty, it should be required
        result = parser.classify_parameter("period", int, inspect.Parameter.empty)
        assert result["param_type"] == "int"
        assert result["required"] is True

        # When default is None, it should not be required (unless Optional)
        result2 = parser.classify_parameter("period", int, None)
        assert result2["param_type"] == "int"
        assert result2["required"] is False  # None as default means optional

    def test_classify_float(self):
        """Test classifying float parameter."""
        parser = TypeParser()
        result = parser.classify_parameter("threshold", float, 0.5)
        assert result["param_type"] == "float"
        assert result["required"] is False
        assert result["default_value"] == 0.5

    def test_classify_string(self):
        """Test classifying string parameter."""
        parser = TypeParser()
        result = parser.classify_parameter("field", str, "close")
        assert result["param_type"] == "string"
        assert result["default_value"] == "close"

    def test_classify_bool(self):
        """Test classifying bool parameter."""
        parser = TypeParser()
        result = parser.classify_parameter("enabled", bool, True)
        assert result["param_type"] == "bool"
        assert result["default_value"] is True

    def test_classify_literal_enum(self):
        """Test classifying Literal type as enum."""
        parser = TypeParser()
        result = parser.classify_parameter("mode", Literal["fast", "slow"], "fast")
        assert result["param_type"] == "enum"
        assert result["options"] == ["fast", "slow"]

    def test_classify_list(self):
        """Test classifying list parameter."""
        parser = TypeParser()
        result = parser.classify_parameter("values", list[int], None)
        assert result["collection"] is True
        assert result["collection_python_type"] is list
        assert result["item_type"] == "int"

    def test_classify_tuple(self):
        """Test classifying tuple parameter."""
        parser = TypeParser()
        result = parser.classify_parameter("pair", tuple[int, int], None)
        assert result["collection"] is True
        assert result["collection_python_type"] is tuple

    def test_classify_optional(self):
        """Test classifying Optional parameter."""
        from typing import Optional

        parser = TypeParser()
        result = parser.classify_parameter("threshold", Optional[float], None)
        assert result["required"] is False

    def test_classify_series_unsupported(self):
        """Test that Series types are marked as unsupported."""
        parser = TypeParser()
        result = parser.classify_parameter("series", Series[Price], None)
        assert result["supported"] is False

    def test_classify_parameter_type_convenience(self):
        """Test convenience function."""
        result = classify_parameter_type(int, 20)
        assert result["param_type"] == "int"
        assert result["default_value"] == 20
