from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Literal

from .io import TAInput, TAOutput
from .spec import IndicatorRequirements


class BaseIndicator(ABC):
    """
    Stateless indicator contract:
      - No instances; use class-level API only.
      - No mutable class attributes.
      - No I/O in compute().
      - Deterministic for given (input, params).
    """

    # Unique, stable name used in registry keys and composition graphs.
    name: ClassVar[str]

    # Hint for schedulers/executors; "stream" can opt into partial bars later.
    kind: ClassVar[Literal["batch", "stream"]] = "batch"

    @classmethod
    @abstractmethod
    def requirements(cls) -> IndicatorRequirements:
        """
        Declarative dependencies (raw data + indicator deps).
        Must return an immutable (or treated-as-immutable) requirements object.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def compute(cls, input: TAInput, **params: Any) -> TAOutput:
        """
        Execute indicator math purely from TAInput and params.
        - No mutation of globals/singletons.
        - No internal state; do not cache here.
        - Engine/planner is responsible for caching and dependency resolution.
        """
        raise NotImplementedError
