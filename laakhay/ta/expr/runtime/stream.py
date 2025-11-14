"""Streaming utilities for incremental expression evaluation."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from ...core.bar import Bar
from ...core.dataset import Dataset
from ...core.ohlcv import OHLCV
from ..algebra import Expression
from ..planner.evaluator import Evaluator


@dataclass(frozen=True)
class AvailabilityTransition:
    """Represents a change in availability mask for an expression output."""

    expression: str
    key: Tuple[str, ...]
    timestamp: Any
    value: Any


@dataclass
class StreamUpdate:
    """Result of a stream update call."""

    outputs: Dict[str, Any] = field(default_factory=dict)
    transitions: List[AvailabilityTransition] = field(default_factory=list)


def _append_bar(ohlcv: OHLCV | None, bar: Bar, *, symbol: str, timeframe: str) -> OHLCV:
    """Append a bar to an OHLCV container, returning a new instance."""
    if ohlcv is None or ohlcv.is_empty:
        return OHLCV(
            timestamps=(bar.ts,),
            opens=(bar.open,),
            highs=(bar.high,),
            lows=(bar.low,),
            closes=(bar.close,),
            volumes=(bar.volume,),
            is_closed=(bar.is_closed,),
            symbol=symbol,
            timeframe=timeframe,
        )

    return OHLCV(
        timestamps=ohlcv.timestamps + (bar.ts,),
        opens=ohlcv.opens + (bar.open,),
        highs=ohlcv.highs + (bar.high,),
        lows=ohlcv.lows + (bar.low,),
        closes=ohlcv.closes + (bar.close,),
        volumes=ohlcv.volumes + (bar.volume,),
        is_closed=ohlcv.is_closed + (bar.is_closed,),
        symbol=ohlcv.symbol,
        timeframe=ohlcv.timeframe,
    )


def _ensure_bar(bar: Bar | Mapping[str, Any]) -> Bar:
    if isinstance(bar, Bar):
        return bar
    return Bar.from_dict(dict(bar))


class Stream:
    """Lightweight helper that tracks expressions over a mutating dataset."""

    def __init__(self, dataset: Dataset | None = None):
        self._dataset = dataset or Dataset()
        self._expressions: dict[str, Expression] = {}
        self._callbacks: dict[str, list[Callable[[AvailabilityTransition], None]]] = {}
        self._evaluator = Evaluator()
        self._last_masks: dict[str, dict[Tuple[str, ...], bool]] = {}
        self._last_lengths: dict[str, dict[Tuple[str, ...], int]] = {}

    @property
    def dataset(self) -> Dataset:
        return self._dataset

    def register(
        self,
        name: str,
        expression: Expression,
        *,
        on_transition: Callable[[AvailabilityTransition], None] | None = None,
    ) -> None:
        """Register an expression to be tracked by the stream."""
        self._expressions[name] = expression
        if on_transition is not None:
            self._callbacks.setdefault(name, []).append(on_transition)
        self._last_masks.setdefault(name, {})

    def on_transition(
        self,
        name: str,
        callback: Callable[[AvailabilityTransition], None],
    ) -> None:
        """Attach an additional transition callback for an expression."""
        self._callbacks.setdefault(name, []).append(callback)

    def update_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        bar: Bar | Mapping[str, Any],
    ) -> StreamUpdate:
        """Append a bar to an OHLCV series and re-evaluate registered expressions."""
        bar_obj = _ensure_bar(bar)
        existing = self._dataset.series(symbol, timeframe, source="ohlcv")

        if existing is not None and not isinstance(existing, OHLCV):
            raise TypeError(f"Existing series for {symbol} {timeframe} is not OHLCV; got {type(existing).__name__}")

        updated = _append_bar(existing, bar_obj, symbol=symbol, timeframe=timeframe)
        self._dataset.add_series(symbol, timeframe, updated, source="ohlcv")
        return self.evaluate()

    def update_series(
        self,
        symbol: str,
        timeframe: str,
        source: str,
        series,
    ) -> StreamUpdate:
        """Replace or add a derived series."""
        self._dataset.add_series(symbol, timeframe, series, source)
        return self.evaluate()

    def evaluate(self) -> StreamUpdate:
        """Evaluate all registered expressions and return outputs + transitions."""
        # Reset evaluator cache so streaming updates reflect latest dataset state.
        self._evaluator = Evaluator()
        outputs: dict[str, Any] = {}
        transitions: list[AvailabilityTransition] = []

        for name, expr in self._expressions.items():
            result = self._evaluator.evaluate(expr, self._dataset)
            outputs[name] = result
            transitions.extend(self._collect_transitions(name, result))

        for transition in transitions:
            for callback in self._callbacks.get(transition.expression, []):
                callback(transition)

        return StreamUpdate(outputs=outputs, transitions=transitions)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_transitions(self, name: str, result: Any) -> list[AvailabilityTransition]:
        transitions: list[AvailabilityTransition] = []
        last_masks = self._last_masks.setdefault(name, {})
        last_lengths = self._last_lengths.setdefault(name, {})

        for key, series in self._iter_series(result):
            if len(series.timestamps) == 0:
                continue

            availability = getattr(series, "availability_mask", None)
            current_len = len(series.timestamps)
            ready = bool(availability[-1]) if availability else current_len > 0

            prev_len = last_lengths.get(key, 0)
            if not ready and current_len > prev_len:
                ready = True

            prev_mask = last_masks.get(key)
            last_masks[key] = ready
            last_lengths[key] = current_len

            if not ready or prev_mask:
                continue

            value = series.values[-1]
            timestamp = series.timestamps[-1]
            transitions.append(
                AvailabilityTransition(
                    expression=name,
                    key=key,
                    timestamp=timestamp,
                    value=value,
                )
            )

        return transitions

    @staticmethod
    def _iter_series(result: Any) -> Iterable[Tuple[Tuple[str, ...], Any]]:
        if isinstance(result, dict):
            for key, series in result.items():
                key_tuple = key if isinstance(key, tuple) else (str(key),)
                yield key_tuple, series
        else:
            yield ("result",), result


__all__ = [
    "Stream",
    "StreamUpdate",
    "AvailabilityTransition",
]
