"""Shared expression execution helpers."""

__all__ = [
    "Engine",
    "DEFAULT_EXECUTION_MODE",
    "resolve_execution_mode",
    "resolve_backend",
    "evaluate_plan",
    "Availability",
    "MissingInputPolicy",
    "ErrorPolicy",
    "StepPolicies",
    "DEFAULT_STEP_POLICIES",
    "StepResult",
    "NodeStepper",
    "build_evaluation_context",
    "collect_required_field_names",
    "resolve_source_from_context",
]


def __getattr__(name: str):
    if name == "Engine":
        from .engine import Engine

        return Engine
    if name in {"DEFAULT_EXECUTION_MODE", "resolve_execution_mode", "resolve_backend"}:
        from .backend import DEFAULT_EXECUTION_MODE, resolve_backend, resolve_execution_mode

        exports = {
            "DEFAULT_EXECUTION_MODE": DEFAULT_EXECUTION_MODE,
            "resolve_execution_mode": resolve_execution_mode,
            "resolve_backend": resolve_backend,
        }
        return exports[name]
    if name == "evaluate_plan":
        from .runner import evaluate_plan

        return evaluate_plan
    if name in {
        "Availability",
        "MissingInputPolicy",
        "ErrorPolicy",
        "StepPolicies",
        "DEFAULT_STEP_POLICIES",
        "StepResult",
        "NodeStepper",
    }:
        from .contracts import (
            DEFAULT_STEP_POLICIES,
            Availability,
            ErrorPolicy,
            MissingInputPolicy,
            NodeStepper,
            StepPolicies,
            StepResult,
        )

        exports = {
            "Availability": Availability,
            "MissingInputPolicy": MissingInputPolicy,
            "ErrorPolicy": ErrorPolicy,
            "StepPolicies": StepPolicies,
            "DEFAULT_STEP_POLICIES": DEFAULT_STEP_POLICIES,
            "StepResult": StepResult,
            "NodeStepper": NodeStepper,
        }
        return exports[name]
    if name in {"build_evaluation_context", "collect_required_field_names", "resolve_source_from_context"}:
        from .context_builder import build_evaluation_context, collect_required_field_names, resolve_source_from_context

        exports = {
            "build_evaluation_context": build_evaluation_context,
            "collect_required_field_names": collect_required_field_names,
            "resolve_source_from_context": resolve_source_from_context,
        }
        return exports[name]
    raise AttributeError(name)
