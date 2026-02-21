"""Parser adapter interface for resolving expression text to Canonical IR."""

from abc import ABC, abstractmethod

from ..ir.nodes import CanonicalExpression


class ParserAdapter(ABC):
    """Abstract base class for expression parsers."""

    @abstractmethod
    def parse_text(self, expression_text: str) -> CanonicalExpression:
        """Parse an expression string into a canonical IR tree."""
        ...
