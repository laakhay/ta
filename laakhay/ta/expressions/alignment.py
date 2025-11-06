"""Alignment policy and context manager for expression evaluation."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Literal


class _Policy(threading.local):
    def __init__(self) -> None:
        self.how: Literal["inner", "outer", "left", "right"] = "inner"
        self.fill: Literal["none", "ffill"] = "none"
        self.left_fill_value: Any | None = None
        self.right_fill_value: Any | None = None


_policy = _Policy()


def get_policy() -> tuple[str, str, Any | None, Any | None]:
    return _policy.how, _policy.fill, _policy.left_fill_value, _policy.right_fill_value


@contextmanager
def alignment(
    *,
    how: Literal["inner", "outer", "left", "right"] | None = None,
    fill: Literal["none", "ffill"] | None = None,
    left_fill_value: Any | None = None,
    right_fill_value: Any | None = None,
):
    """Temporarily override default alignment policy for expressions.

    Usage:
        with alignment(how="outer", fill="ffill"):
            expr.run(ds)
    """
    prev = (
        _policy.how,
        _policy.fill,
        _policy.left_fill_value,
        _policy.right_fill_value,
    )
    try:
        if how is not None:
            _policy.how = how
        if fill is not None:
            _policy.fill = fill
        if left_fill_value is not None:
            _policy.left_fill_value = left_fill_value
        if right_fill_value is not None:
            _policy.right_fill_value = right_fill_value
        yield
    finally:
        _policy.how, _policy.fill, _policy.left_fill_value, _policy.right_fill_value = prev
