"""Tests for catalog building functionality."""

import pytest

from laakhay.ta.catalog import CatalogBuilder, describe_indicator, list_catalog


class TestCatalogBuilder:
    """Test CatalogBuilder class."""

    def test_build_catalog(self):
        """Test building complete catalog."""
        builder = CatalogBuilder()
        catalog = builder.build_catalog()

        assert isinstance(catalog, dict)
        assert len(catalog) > 0
        # Check for common indicators
        assert "sma" in catalog
        assert "ema" in catalog
        assert "rsi" in catalog

    def test_describe_indicator(self):
        """Test describing a single indicator."""
        builder = CatalogBuilder()
        registry = builder._registry
        handle = registry.get("sma")
        assert handle is not None

        descriptor = builder.describe_indicator("sma", handle)
        assert descriptor.name == "sma"
        assert descriptor.category == "trend"
        assert len(descriptor.parameters) > 0
        assert len(descriptor.outputs) > 0
        assert descriptor.supported is True

    def test_describe_indicator_parameters(self):
        """Test that indicator parameters are correctly extracted."""
        builder = CatalogBuilder()
        registry = builder._registry
        handle = registry.get("sma")
        assert handle is not None

        descriptor = builder.describe_indicator("sma", handle)
        # SMA should have period parameter
        param_names = [p.name for p in descriptor.parameters]
        assert "period" in param_names

    def test_describe_indicator_outputs(self):
        """Test that indicator outputs are correctly extracted."""
        builder = CatalogBuilder()
        registry = builder._registry
        handle = registry.get("macd")
        assert handle is not None

        descriptor = builder.describe_indicator("macd", handle)
        # MACD should have multiple outputs
        assert len(descriptor.outputs) >= 1
        assert descriptor.tuple_aliases == ("macd", "signal", "histogram")

    def test_describe_indicator_category(self):
        """Test that indicator categories are inferred correctly."""
        builder = CatalogBuilder()
        registry = builder._registry

        sma_handle = registry.get("sma")
        assert sma_handle is not None
        sma_descriptor = builder.describe_indicator("sma", sma_handle)
        assert sma_descriptor.category == "trend"

        rsi_handle = registry.get("rsi")
        assert rsi_handle is not None
        rsi_descriptor = builder.describe_indicator("rsi", rsi_handle)
        assert rsi_descriptor.category == "momentum"

    def test_param_map_built(self):
        """Test that parameter map is built correctly."""
        builder = CatalogBuilder()
        registry = builder._registry
        handle = registry.get("sma")
        assert handle is not None

        descriptor = builder.describe_indicator("sma", handle)
        assert "period" in descriptor.param_map
        assert descriptor.param_map["period"].name == "period"


class TestCatalogConvenience:
    """Test convenience functions."""

    def test_list_catalog(self):
        """Test list_catalog convenience function."""
        catalog = list_catalog()

        assert isinstance(catalog, dict)
        assert len(catalog) > 0
        assert "sma" in catalog

    def test_describe_indicator_convenience(self):
        """Test describe_indicator convenience function."""
        descriptor = describe_indicator("sma")

        assert descriptor.name == "sma"
        assert descriptor.category == "trend"
        assert len(descriptor.parameters) > 0

    def test_describe_indicator_not_found(self):
        """Test describe_indicator raises error for unknown indicator."""
        with pytest.raises(ValueError, match="not found"):
            describe_indicator("unknown_indicator")

    def test_catalog_includes_indicators(self):
        """Test that catalog includes various indicator types."""
        catalog = list_catalog()

        # Trend indicators
        assert "sma" in catalog
        assert "ema" in catalog
        assert "macd" in catalog

        # Momentum indicators
        assert "rsi" in catalog
        assert "stochastic" in catalog

        # Volatility indicators
        assert "atr" in catalog
        assert "bbands" in catalog

        # Volume indicators
        assert "obv" in catalog
        assert "vwap" in catalog

    def test_catalog_descriptor_structure(self):
        """Test that catalog descriptors have correct structure."""
        catalog = list_catalog()
        descriptor = catalog["sma"]

        assert hasattr(descriptor, "name")
        assert hasattr(descriptor, "description")
        assert hasattr(descriptor, "category")
        assert hasattr(descriptor, "parameters")
        assert hasattr(descriptor, "outputs")
        assert hasattr(descriptor, "supported")
        assert hasattr(descriptor, "handle")
        assert hasattr(descriptor, "param_map")
        assert hasattr(descriptor, "get_parameter_specs")

    def test_get_parameter_specs(self):
        """Test that get_parameter_specs returns correct format."""
        catalog = list_catalog()
        descriptor = catalog["sma"]
        specs = descriptor.get_parameter_specs()

        assert isinstance(specs, dict)
        assert "period" in specs
        assert isinstance(specs["period"], dict)
        assert "param_type" in specs["period"]
        assert "required" in specs["period"]

    def test_bbands_output_metadata_exposed_in_catalog(self):
        """Test that bbands outputs and their metadata are present in the catalog."""
        catalog = list_catalog()
        descriptor = catalog["bbands"]

        # Expect three outputs: upper, middle, lower
        output_names = {out.name for out in descriptor.outputs}
        assert output_names == {"upper", "middle", "lower"}

        meta_by_name = {out.name: out.metadata or {} for out in descriptor.outputs}

        assert meta_by_name["upper"].get("role") == "band_upper"
        assert meta_by_name["upper"].get("area_pair") == "lower"

        assert meta_by_name["middle"].get("role") == "band_middle"

        assert meta_by_name["lower"].get("role") == "band_lower"
        assert meta_by_name["lower"].get("area_pair") == "upper"

    def test_macd_output_metadata_exposed_in_catalog(self):
        """Test that macd outputs and their metadata are present in the catalog."""
        catalog = list_catalog()
        descriptor = catalog["macd"]

        output_names = {out.name for out in descriptor.outputs}
        # macd, signal, histogram
        assert {"macd", "signal", "histogram"} <= output_names

        meta_by_name = {out.name: out.metadata or {} for out in descriptor.outputs}
        assert meta_by_name["macd"].get("role") == "line"
        assert meta_by_name["signal"].get("role") == "signal"
        assert meta_by_name["histogram"].get("role") == "histogram"

    def test_stochastic_output_metadata_exposed_in_catalog(self):
        """Test that stochastic outputs and their metadata are present in the catalog."""
        catalog = list_catalog()
        descriptor = catalog["stochastic"]

        output_names = {out.name for out in descriptor.outputs}
        # k and d lines
        assert {"k", "d"} <= output_names

        meta_by_name = {out.name: out.metadata or {} for out in descriptor.outputs}
        assert meta_by_name["k"].get("role") == "osc_main"
        assert meta_by_name["d"].get("role") == "osc_signal"

    def test_all_indicators_have_output_roles(self):
        """All indicators in the catalog should have role metadata on each output."""
        catalog = list_catalog()
        for name, descriptor in catalog.items():
            assert descriptor.outputs, f"Indicator {name} should have at least one output"
            for out in descriptor.outputs:
                assert out.metadata is not None, f"Indicator {name} output {out.name} missing metadata"
                assert "role" in out.metadata, f"Indicator {name} output {out.name} missing 'role' metadata"

    def test_volume_indicators_have_volume_role(self):
        """Volume-category indicators should expose 'volume' role for outputs."""
        catalog = list_catalog()

        # OBV and VWAP are categorized as volume indicators
        for name in ("obv", "vwap"):
            descriptor = catalog[name]
            assert descriptor.category == "volume"
            assert descriptor.outputs, f"{name} should have at least one output"
            for out in descriptor.outputs:
                role = (out.metadata or {}).get("role")
                assert role == "volume", f"{name} output {out.name} should have 'volume' role, got {role!r}"
