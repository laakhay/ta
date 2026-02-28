from __future__ import annotations

from pathlib import Path


def test_ffi_header_exists_and_has_abi_symbol() -> None:
    header = Path("../crates/ta-ffi/include/ta_engine.h")
    assert header.exists()
    content = header.read_text()
    assert "ta_engine_abi_version" in content
    assert "TA_STATUS_OK" in content
