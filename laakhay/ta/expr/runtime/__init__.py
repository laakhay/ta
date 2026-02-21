"""Runtime compatibility APIs for evaluation, preview, validation, and streaming.

Note: ``RuntimeEvaluator`` is a legacy compatibility wrapper. Canonical
evaluation logic lives in ``laakhay.ta.expr.planner.evaluator.Evaluator``.
"""

from .analyze import AnalysisResult, analyze
from .emission import IndicatorEmission, IndicatorInputBinding, IndicatorRenderHints
from .engine import Engine
from .legacy_evaluator import RuntimeEvaluator
from .legacy_evaluator import RuntimeEvaluator as LegacyRuntimeEvaluator
from .preview import PreviewResult, preview
from .stream import AvailabilityTransition, Stream, StreamUpdate
from .validate import ExprValidationError, ValidationResult, validate

__all__ = [
    "Engine",
    "RuntimeEvaluator",
    "LegacyRuntimeEvaluator",
    "preview",
    "PreviewResult",
    "IndicatorEmission",
    "IndicatorInputBinding",
    "IndicatorRenderHints",
    "validate",
    "ValidationResult",
    "ExprValidationError",
    "Stream",
    "StreamUpdate",
    "AvailabilityTransition",
    "analyze",
    "AnalysisResult",
]
