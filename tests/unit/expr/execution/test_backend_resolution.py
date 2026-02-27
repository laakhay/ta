from __future__ import annotations

import pytest

from laakhay.ta.expr.execution.backend import (
    DEFAULT_INCREMENTAL_BACKEND,
    resolve_backend,
    resolve_incremental_backend_mode,
)
from laakhay.ta.expr.execution.backends.batch import BatchBackend
from laakhay.ta.expr.execution.backends.incremental import IncrementalBackend
from laakhay.ta.expr.execution.backends.incremental_rust import IncrementalRustBackend


def test_default_incremental_backend_is_rust() -> None:
    assert DEFAULT_INCREMENTAL_BACKEND == "rust"


def test_resolve_incremental_backend_mode_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TA_INCREMENTAL_BACKEND", raising=False)
    assert resolve_incremental_backend_mode() == "rust"


def test_resolve_incremental_backend_mode_python(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TA_INCREMENTAL_BACKEND", "python")
    assert resolve_incremental_backend_mode() == "python"


def test_resolve_incremental_backend_mode_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TA_INCREMENTAL_BACKEND", "bad")
    with pytest.raises(ValueError, match="Unsupported incremental backend"):
        resolve_incremental_backend_mode()


def test_resolve_backend_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TA_INCREMENTAL_BACKEND", raising=False)
    backend = resolve_backend("batch")
    assert isinstance(backend, BatchBackend)


def test_resolve_backend_incremental_rust(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TA_INCREMENTAL_BACKEND", "rust")
    backend = resolve_backend("incremental")
    assert isinstance(backend, IncrementalRustBackend)


def test_resolve_backend_incremental_python(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TA_INCREMENTAL_BACKEND", "python")
    backend = resolve_backend("incremental")
    assert isinstance(backend, IncrementalBackend)
