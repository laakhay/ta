"""Market signals and pattern detection."""

from .spikes import (
    CombinedSpikeDetector,
    CombinedSpikeResult,
    PriceSpikeDetector,
    PriceSpikeResult,
    VolumeSpikeDetector,
    VolumeSpikeResult,
)

__all__ = [
    "PriceSpikeDetector",
    "PriceSpikeResult",
    "VolumeSpikeDetector",
    "VolumeSpikeResult",
    "CombinedSpikeDetector",
    "CombinedSpikeResult",
]
