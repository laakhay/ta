"""Canonical execution contracts for step-based expression evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, Protocol, TypeVar

StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")


class Availability(StrEnum):
    """Availability state for step outputs."""

    READY = "ready"
    WARMING_UP = "warming_up"
    MISSING_INPUT = "missing_input"
    ERROR = "error"


class MissingInputPolicy(StrEnum):
    """Policy for handling missing upstream inputs."""

    EMIT_MISSING = "emit_missing"
    HOLD_PREVIOUS = "hold_previous"
    FAIL = "fail"


class ErrorPolicy(StrEnum):
    """Policy for handling runtime step errors."""

    RAISE = "raise"
    EMIT_ERROR = "emit_error"
    EMIT_MISSING = "emit_missing"


@dataclass(frozen=True)
class StepPolicies:
    """Shared policies for missing inputs and runtime errors."""

    missing_input: MissingInputPolicy = MissingInputPolicy.EMIT_MISSING
    on_error: ErrorPolicy = ErrorPolicy.RAISE


DEFAULT_STEP_POLICIES = StepPolicies()


@dataclass(frozen=True)
class StepResult(Generic[StateT, OutputT]):
    """Result of a single node step.

    `output` can be `None` for warmup/missing-input/error phases. The
    `availability` field is the canonical source of truth for downstream behavior.
    """

    next_state: StateT
    output: OutputT | None
    availability: Availability
    error: str | None = None

    @property
    def is_ready(self) -> bool:
        return self.availability is Availability.READY

    @classmethod
    def ready(cls, next_state: StateT, output: OutputT) -> StepResult[StateT, OutputT]:
        return cls(next_state=next_state, output=output, availability=Availability.READY)

    @classmethod
    def warming_up(cls, next_state: StateT) -> StepResult[StateT, OutputT]:
        return cls(next_state=next_state, output=None, availability=Availability.WARMING_UP)

    @classmethod
    def missing_input(cls, next_state: StateT) -> StepResult[StateT, OutputT]:
        return cls(next_state=next_state, output=None, availability=Availability.MISSING_INPUT)

    @classmethod
    def errored(cls, next_state: StateT, error: str) -> StepResult[StateT, OutputT]:
        return cls(next_state=next_state, output=None, availability=Availability.ERROR, error=error)


class NodeStepper(Protocol[StateT, OutputT]):
    """Protocol every step-capable node adapter should satisfy."""

    def step(self, state: StateT, update: Any, /, **kwargs: Any) -> StepResult[StateT, OutputT]:
        """Compute next state and output for one update event."""
        ...
