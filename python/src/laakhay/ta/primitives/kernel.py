from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable, Protocol, TypeVar

S = TypeVar("S")


class Kernel(Protocol[S]):
    """A unified protocol for both batch and incremental indicator execution.

    Kernels define the core mathematical state transitions for an indicator,
    decoupled from how the data is iterated (e.g., vectorized batch vs.
    tick-by-tick streaming).
    """

    def initialize(self, history: list[Any], **params: Any) -> S:
        """Initialize the kernel state from a warm-up history window.

        Args:
            history: A list of previous data points (e.g., length equals the period).
                     May be smaller than the required period if not enough data exists.
            **params: Indicator parameters (e.g., period, std_dev).

        Returns:
            The initial state object.
        """
        ...

    def step(self, state: S, x_t: Any, **params: Any) -> tuple[S, Decimal]:
        """Process a single new data point and return the updated state and output.

        Args:
            state: The current state of the kernel.
            x_t: The new incoming data point at time t.
            **params: Indicator parameters.

        Returns:
            A tuple of (new_state, output_value).
        """
        ...


def run_kernel(
    src: Any,
    kernel: Kernel[Any],
    min_periods: int = 1,
    coerce_input: Callable[[Any], Any] | None = None,
    **params: Any,
) -> Any:
    """Execute a kernel over a batch series, preserving exact batch semantics.

    Args:
        src: The source Series[Price]
        kernel: The initialized kernel instance
        min_periods: The number of periods required before producing the first output.
                     For EMA this is 1. For SMA this is `period`.
        **params: Passed to initialize and step.
    """
    from ..core import Series
    from ..core.types import Price

    n = len(src.values)
    if n == 0:
        return Series[Price](timestamps=(), values=(), symbol=src.symbol, timeframe=src.timeframe)

    if coerce_input is None:

        def _default_coerce_input(v: Any) -> Decimal:
            return Decimal(str(v))

        coerce_input = _default_coerce_input

    xs = [coerce_input(v) for v in src.values]
    out: list[Any] = [Decimal("NaN")] * n

    warmup_len = max(0, min_periods - 1)
    mask = [False] * n
    if n >= min_periods:
        state = kernel.initialize(xs[:warmup_len], **params)

        for i in range(warmup_len, n):
            state, val = kernel.step(state, xs[i], **params)
            out[i] = val
            mask[i] = True

    return Series[Price](
        timestamps=src.timestamps,
        values=tuple(Price(v) if v is not None else Price("NaN") for v in out),
        symbol=src.symbol,
        timeframe=src.timeframe,
        availability_mask=tuple(mask),
    )
