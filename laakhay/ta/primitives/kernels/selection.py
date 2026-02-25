from dataclasses import dataclass
from typing import Any

from ..kernel import Kernel


@dataclass(frozen=True)
class SelectionState:
    pass


class SelectionKernel(Kernel[SelectionState]):
    def initialize(self, history: list[Any], **kwargs: Any) -> SelectionState:
        return SelectionState()

    def step(self, state: SelectionState, input_val: Any, **kwargs: Any) -> tuple[SelectionState, Any]:
        # input_val is whatever the first child returned.
        # For select(field='close'), first child usually doesn't exist in DSL sense
        # but eval_call_step might be passing something.
        # Actually, select() in dsl/parser.py is:
        # CallNode(name="select", args=(), kwargs={"field": LiteralNode(...)})
        # So children_vals is empty.
        # The value we want is in the 'tick' dict.
        # BUT eval_call_step only passes 'input_val' (children_vals[0]).

        # Wait! I should check eval_call_step again.
        # It has access to 'tick'!
        pass
