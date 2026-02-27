from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class TaStatusCode(IntEnum):
    OK = 0
    INVALID_INPUT = 1
    SHAPE_MISMATCH = 2
    INTERNAL_ERROR = 255


@dataclass(frozen=True)
class RuntimeSeriesF64:
    values: tuple[float, ...]
    availability_mask: tuple[bool, ...]

    def __post_init__(self) -> None:
        if len(self.values) != len(self.availability_mask):
            raise ValueError("values and availability_mask must have identical lengths")

    @property
    def length(self) -> int:
        return len(self.values)


__all__ = [
    "RuntimeSeriesF64",
    "TaStatusCode",
]
