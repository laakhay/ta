"""State models for incremental kernel execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class KernelState:
    """Holds the active execution state for a single IR node instance."""

    # The internal algorithm state for the kernel (e.g. RollingState, EMAState)
    algorithm_state: Any | None = None

    # Track the number of data points processed by this node
    ticks_processed: int = 0

    # Store the most recently produced output value
    last_value: Decimal | None = None

    # Whether this node has generated enough data to be considered "valid"
    is_valid: bool = False

    # Historical output window (useful if downstream nodes need lookback)
    # Not always strictly necessary depending on the global DAG traversal strategy,
    # but helpful for cross-sectional references.
    history: list[Decimal] = field(default_factory=list)
