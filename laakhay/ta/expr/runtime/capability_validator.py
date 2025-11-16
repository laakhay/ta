"""Capability validation helpers for expression validation.

Warns when expressions reference sources/fields that the configured
backend cannot provide, using the capability manifest.
"""

from __future__ import annotations

from typing import Any

from ..planner.manifest import generate_capability_manifest
from ..planner.types import PlanResult, SignalRequirements


class CapabilityValidator:
    """Validates expression requirements against backend capabilities.

    Uses the capability manifest to check if required sources/fields
    are available from the configured backend.
    """

    def __init__(self, manifest: dict[str, Any] | None = None):
        """Initialize validator with capability manifest.

        Args:
            manifest: Optional capability manifest. If None, generates one.
        """
        self.manifest = manifest or generate_capability_manifest()
        self._sources = self.manifest.get("sources", {})
        self._exchange_support = self.manifest.get("exchange_source_support", {})

    def validate_requirements(
        self,
        requirements: SignalRequirements,
        exchange: str | None = None,
    ) -> list[str]:
        """Validate data requirements against backend capabilities.

        Args:
            requirements: SignalRequirements from expression planning
            exchange: Optional exchange name to check exchange-specific support

        Returns:
            List of warning messages for unsupported requirements
        """
        warnings: list[str] = []

        # Check data requirements
        for req in requirements.data_requirements:
            source = req.source
            field = req.field

            # Check if source is supported
            if source not in self._sources:
                warnings.append(
                    f"Source '{source}' is not available. Available sources: {', '.join(self._sources.keys())}"
                )
                continue

            # Check if field is supported for this source
            source_fields = self._sources[source].get("fields", [])
            if field not in source_fields:
                warnings.append(
                    f"Field '{field}' is not available for source '{source}'. "
                    f"Available fields: {', '.join(source_fields)}"
                )

            # Check exchange-specific support if exchange is specified
            if exchange and exchange in self._exchange_support:
                exchange_sources = self._exchange_support[exchange]
                if source in exchange_sources:
                    support = exchange_sources[source]
                    if not support.get("rest", False) and not support.get("ws", False):
                        warnings.append(
                            f"Source '{source}' is not supported by exchange '{exchange}'. Required for field '{field}'"
                        )

        # Check required sources
        for source in requirements.required_sources:
            if source not in self._sources:
                warnings.append(
                    f"Source '{source}' is not available. Available sources: {', '.join(self._sources.keys())}"
                )

        # Check required exchanges
        for req_exchange in requirements.required_exchanges:
            if req_exchange not in self._exchange_support:
                warnings.append(
                    f"Exchange '{req_exchange}' capabilities are not known. "
                    f"Available exchanges: {', '.join(self._exchange_support.keys())}"
                )

        return warnings

    def validate_plan(
        self,
        plan: PlanResult,
        exchange: str | None = None,
    ) -> list[str]:
        """Validate a PlanResult against backend capabilities.

        Args:
            plan: PlanResult from expression planning
            exchange: Optional exchange name to check exchange-specific support

        Returns:
            List of warning messages for unsupported requirements
        """
        return self.validate_requirements(plan.requirements, exchange=exchange)

    def check_source_support(
        self,
        source: str,
        field: str | None = None,
        exchange: str | None = None,
    ) -> tuple[bool, str | None]:
        """Check if a source (and optionally field) is supported.

        Args:
            source: Source name (e.g., 'ohlcv', 'trades')
            field: Optional field name
            exchange: Optional exchange name for exchange-specific checks

        Returns:
            Tuple of (is_supported, error_message)
        """
        if source not in self._sources:
            return False, f"Source '{source}' is not available. Available: {', '.join(self._sources.keys())}"

        if field:
            source_fields = self._sources[source].get("fields", [])
            if field not in source_fields:
                return False, (
                    f"Field '{field}' is not available for source '{source}'. "
                    f"Available fields: {', '.join(source_fields)}"
                )

        if exchange and exchange in self._exchange_support:
            exchange_sources = self._exchange_support[exchange]
            if source in exchange_sources:
                support = exchange_sources[source]
                if not support.get("rest", False) and not support.get("ws", False):
                    return False, f"Source '{source}' is not supported by exchange '{exchange}'"

        return True, None

    def check_indicator_source_compatibility(
        self,
        indicator: str,
        source: str,
        field: str | None = None,
    ) -> tuple[bool, str | None]:
        """Check if an indicator is compatible with a given source/field.

        Args:
            indicator: Indicator name
            source: Source name
            field: Optional field name

        Returns:
            Tuple of (is_compatible, reason_if_not)
        """
        # Get indicator metadata
        from ...registry.registry import get_global_registry

        registry = get_global_registry()
        handle = registry.get(indicator)
        if not handle:
            return False, f"Indicator '{indicator}' not found in registry"

        # Check if source is supported
        is_supported, error = self.check_source_support(source, field)
        if not is_supported:
            return False, error

        # For now, most indicators work with any numeric series
        # In the future, we could add indicator-specific source/field restrictions
        return True, None
