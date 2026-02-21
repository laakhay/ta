"""Execution state models and snapshot metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

STATE_SCHEMA_VERSION = 1


@dataclass
class KernelState:
    """Holds the active execution state for a single IR node instance."""

    algorithm_state: Any | None = None
    ticks_processed: int = 0
    last_value: Decimal | None = None
    is_valid: bool = False
    history: list[Decimal] = field(default_factory=list)


@dataclass(frozen=True)
class StateSnapshot:
    """Versioned snapshot payload for execution state store."""

    schema_version: int
    states: dict[int, KernelState]
