from __future__ import annotations

from laakhay.ta.runtime.backend import RuntimeBackend, get_runtime_backend


def test_backend_defaults_to_rust(monkeypatch):
    monkeypatch.delenv("LAAKHAY_TA_BACKEND", raising=False)
    assert get_runtime_backend() == RuntimeBackend.RUST


def test_backend_can_be_forced_to_python(monkeypatch):
    monkeypatch.setenv("LAAKHAY_TA_BACKEND", "python")
    assert get_runtime_backend() == RuntimeBackend.RUST
