from typing import Any

from laakhay.ta.expr.execution import (
    DEFAULT_STEP_POLICIES,
    Availability,
    ErrorPolicy,
    MissingInputPolicy,
    NodeStepper,
    StepResult,
)


def test_step_result_ready_factory() -> None:
    result = StepResult[dict[str, Any], int].ready({"n": 1}, 42)
    assert result.next_state == {"n": 1}
    assert result.output == 42
    assert result.availability is Availability.READY
    assert result.is_ready
    assert result.error is None


def test_step_result_non_ready_factories() -> None:
    warm = StepResult[dict[str, Any], int].warming_up({"n": 1})
    missing = StepResult[dict[str, Any], int].missing_input({"n": 2})
    err = StepResult[dict[str, Any], int].errored({"n": 3}, "boom")

    assert warm.availability is Availability.WARMING_UP and not warm.is_ready
    assert warm.output is None

    assert missing.availability is Availability.MISSING_INPUT and not missing.is_ready
    assert missing.output is None

    assert err.availability is Availability.ERROR and not err.is_ready
    assert err.output is None
    assert err.error == "boom"


def test_default_step_policies_are_explicit() -> None:
    assert DEFAULT_STEP_POLICIES.missing_input is MissingInputPolicy.EMIT_MISSING
    assert DEFAULT_STEP_POLICIES.on_error is ErrorPolicy.RAISE


def test_node_stepper_protocol_shape() -> None:
    class DummyStepper:
        def step(self, state: int, update: Any, /, **kwargs: Any) -> StepResult[int, int]:
            return StepResult.ready(state + 1, state + int(update))

    stepper: NodeStepper[int, int] = DummyStepper()
    out = stepper.step(1, 2)
    assert out.next_state == 2
    assert out.output == 3
    assert out.availability is Availability.READY
