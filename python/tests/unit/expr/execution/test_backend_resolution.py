from __future__ import annotations

import pytest

from laakhay.ta.expr.execution.backend import resolve_backend
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend


def test_resolve_backend_incremental_uses_rust(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TA_INCREMENTAL_BACKEND", "python")
    backend = resolve_backend("incremental")
    assert isinstance(backend, IncrementalRustBackend)


def test_resolve_backend_rejects_batch_mode() -> None:
    with pytest.raises(ValueError, match="Expected 'incremental'"):
        resolve_backend("batch")
