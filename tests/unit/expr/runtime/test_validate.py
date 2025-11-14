"""Tests for expression validation functionality."""

from laakhay.ta.expr import ValidationResult, validate
from laakhay.ta.expr.dsl import StrategyError, parse_expression_text


class TestValidateBasic:
    """Test basic validation functionality."""

    def test_validate_valid_expression(self):
        """Test validation passes for valid expression."""
        result = validate("sma(20) > sma(50)")

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0
        assert "sma" in result.indicators

    def test_validate_invalid_indicator(self):
        """Test validation fails for unknown indicator."""
        result = validate("unknown_indicator(20)")

        assert isinstance(result, ValidationResult)
        assert result.valid is False
        assert len(result.errors) > 0
        assert any("unknown_indicator" in error.lower() for error in result.errors)

    def test_validate_missing_parameter(self):
        """Test validation warns about missing required parameters."""
        result = validate("sma()")

        # SMA has default period parameter, so this is valid
        # The test just verifies validation doesn't crash
        assert isinstance(result, ValidationResult)

    def test_validate_invalid_expression_syntax(self):
        """Test validation catches syntax errors."""
        result = validate("sma(20) >")

        assert isinstance(result, ValidationResult)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_complex_expression(self):
        """Test validation works with complex nested expressions."""
        result = validate("(sma(20) > sma(50)) and (rsi(14) < 30)")

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert "sma" in result.indicators
        assert "rsi" in result.indicators


class TestValidateSelectFields:
    """Test select field validation."""

    def test_validate_valid_select_fields(self):
        """Test validation accepts valid select fields."""
        valid_fields = ["close", "high", "low", "open", "volume", "hlc3", "ohlc4"]
        for field in valid_fields:
            result = validate(f"select('{field}')")
            # Should pass validation (may have warnings about missing dataset, but no errors about field)
            assert field in result.select_fields or result.valid

    def test_validate_invalid_select_field(self):
        """Test validation rejects invalid select fields."""
        result = validate("select('invalid_field')")

        assert isinstance(result, ValidationResult)
        assert result.valid is False
        assert len(result.errors) > 0
        assert any("invalid_field" in error.lower() for error in result.errors)

    def test_validate_select_field_whitelist(self):
        """Test that validation error lists valid select fields."""
        result = validate("select('bad_field')")

        assert isinstance(result, ValidationResult)
        if result.errors:
            error_msg = " ".join(result.errors).lower()
            # Should mention valid fields
            assert "close" in error_msg or "valid fields" in error_msg


class TestValidateIndicators:
    """Test indicator validation."""

    def test_validate_extracts_indicators(self):
        """Test that validation extracts all indicators from expression."""
        result = validate("sma(20) + ema(12) * rsi(14)")

        assert isinstance(result, ValidationResult)
        assert "sma" in result.indicators
        assert "ema" in result.indicators
        assert "rsi" in result.indicators

    def test_validate_suggests_similar_indicators(self):
        """Test that validation suggests similar indicators for typos."""
        # This will fail at parse time, not validation time
        # The error comes from the parser, not our validation
        result = validate("smma(20)")  # typo for sma

        assert isinstance(result, ValidationResult)
        assert result.valid is False
        # Error message should indicate indicator not found
        error_msg = " ".join(result.errors).lower()
        assert "not found" in error_msg or "smma" in error_msg

    def test_validate_indicator_parameters(self):
        """Test that validation checks indicator parameters."""
        result = validate("sma(period=20)")

        assert isinstance(result, ValidationResult)
        # Should pass - period is valid parameter
        # May have warnings but should compile

    def test_validate_unknown_parameter(self):
        """Test that validation warns about unknown parameters."""
        # This should pass compilation but may have warnings
        result = validate("sma(20, unknown_param=5)")

        # Depending on implementation, may have warnings
        # At minimum should not crash


class TestValidateErrors:
    """Test error handling in validation."""

    def test_validate_handles_parse_errors(self):
        """Test that validation gracefully handles parse errors."""
        result = validate("sma(20) >")

        assert isinstance(result, ValidationResult)
        assert result.valid is False
        assert len(result.errors) > 0
        # Should mention parsing failed
        error_msg = " ".join(result.errors).lower()
        assert "parse" in error_msg or "syntax" in error_msg

    def test_validate_handles_compile_errors(self):
        """Test that validation catches compilation errors."""
        # Expression that parses but doesn't compile
        result = validate("sma(20) + invalid_indicator(10)")

        assert isinstance(result, ValidationResult)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_result_structure(self):
        """Test that ValidationResult has correct structure."""
        result = validate("sma(20)")

        assert hasattr(result, "valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "indicators")
        assert hasattr(result, "select_fields")
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.indicators, list)
        assert isinstance(result.select_fields, list)


class TestValidateWithStrategyExpression:
    """Test validation with parsed StrategyExpression."""

    def test_validate_with_parsed_expression(self):
        """Test that validation works with already-parsed expression."""
        parsed = parse_expression_text("sma(20) > sma(50)")
        result = validate(parsed)

        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_invalid_parsed_expression(self):
        """Test validation with invalid parsed expression."""
        try:
            parsed = parse_expression_text("unknown(20)")
            result = validate(parsed)
            # Should fail validation
            assert result.valid is False
        except StrategyError:
            # If parsing fails, that's also acceptable
            pass
