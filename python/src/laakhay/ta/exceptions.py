"""Dedicated exception types for laakhay-ta library.

Provides structured error types with context for easier debugging
and better error handling in downstream services.
"""

from __future__ import annotations

from typing import Any


class TAError(Exception):
    """Base exception for all laakhay-ta errors."""

    pass


class MissingDataError(TAError):
    """Raised when required data is missing from dataset.

    Attributes:
        source: Data source type (e.g., 'ohlcv', 'trades', 'orderbook')
        field: Field name that was requested
        symbol: Trading symbol (if applicable)
        exchange: Exchange name (if applicable)
        timeframe: Timeframe (if applicable)
    """

    def __init__(
        self,
        message: str,
        source: str | None = None,
        field: str | None = None,
        symbol: str | None = None,
        exchange: str | None = None,
        timeframe: str | None = None,
    ):
        super().__init__(message)
        self.source = source
        self.field = field
        self.symbol = symbol
        self.exchange = exchange
        self.timeframe = timeframe

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.source:
            parts.append(f"source={self.source}")
        if self.field:
            parts.append(f"field={self.field}")
        if self.symbol:
            parts.append(f"symbol={self.symbol}")
        if self.exchange:
            parts.append(f"exchange={self.exchange}")
        if self.timeframe:
            parts.append(f"timeframe={self.timeframe}")
        return " | ".join(parts)


class UnsupportedSourceError(TAError):
    """Raised when a data source is not supported.

    Attributes:
        source: Data source type that is not supported
        symbol: Trading symbol (if applicable)
        exchange: Exchange name (if applicable)
        available_sources: List of available sources
    """

    def __init__(
        self,
        message: str,
        source: str,
        symbol: str | None = None,
        exchange: str | None = None,
        available_sources: list[str] | None = None,
    ):
        super().__init__(message)
        self.source = source
        self.symbol = symbol
        self.exchange = exchange
        self.available_sources = available_sources or []

    def __str__(self) -> str:
        parts = [super().__str__()]
        parts.append(f"source={self.source}")
        if self.symbol:
            parts.append(f"symbol={self.symbol}")
        if self.exchange:
            parts.append(f"exchange={self.exchange}")
        if self.available_sources:
            parts.append(f"available={', '.join(self.available_sources)}")
        return " | ".join(parts)


class UnsupportedIndicatorError(TAError):
    """Raised when an indicator is not supported for a given source/field combination.

    Attributes:
        indicator: Indicator name
        source: Data source type
        field: Field name
        reason: Reason why the combination is not supported
    """

    def __init__(
        self,
        message: str,
        indicator: str,
        source: str | None = None,
        field: str | None = None,
        reason: str | None = None,
    ):
        super().__init__(message)
        self.indicator = indicator
        self.source = source
        self.field = field
        self.reason = reason

    def __str__(self) -> str:
        parts = [super().__str__()]
        parts.append(f"indicator={self.indicator}")
        if self.source:
            parts.append(f"source={self.source}")
        if self.field:
            parts.append(f"field={self.field}")
        if self.reason:
            parts.append(f"reason={self.reason}")
        return " | ".join(parts)


class EvaluationError(TAError):
    """Raised when expression evaluation fails.

    Attributes:
        expression: Expression that failed to evaluate
        node_type: Type of node that caused the failure
        context: Additional context about the failure
    """

    def __init__(
        self,
        message: str,
        expression: str | None = None,
        node_type: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.expression = expression
        self.node_type = node_type
        self.context = context or {}

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.expression:
            parts.append(f"expression={self.expression}")
        if self.node_type:
            parts.append(f"node_type={self.node_type}")
        return " | ".join(parts)


class AlignmentError(TAError):
    """Raised when series alignment fails.

    Attributes:
        left_symbol: Symbol of left series
        left_timeframe: Timeframe of left series
        right_symbol: Symbol of right series
        right_timeframe: Timeframe of right series
        reason: Reason for alignment failure
    """

    def __init__(
        self,
        message: str,
        left_symbol: str | None = None,
        left_timeframe: str | None = None,
        right_symbol: str | None = None,
        right_timeframe: str | None = None,
        reason: str | None = None,
    ):
        super().__init__(message)
        self.left_symbol = left_symbol
        self.left_timeframe = left_timeframe
        self.right_symbol = right_symbol
        self.right_timeframe = right_timeframe
        self.reason = reason

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.left_symbol:
            parts.append(f"left=({self.left_symbol}, {self.left_timeframe})")
        if self.right_symbol:
            parts.append(f"right=({self.right_symbol}, {self.right_timeframe})")
        if self.reason:
            parts.append(f"reason={self.reason}")
        return " | ".join(parts)
