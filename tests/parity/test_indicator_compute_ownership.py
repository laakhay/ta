from __future__ import annotations

import pytest

from laakhay.ta.catalog import list_catalog_metadata
from laakhay.ta.catalog.rust_catalog import rust_catalog_available
from laakhay.ta.catalog.porting_matrix import INDICATOR_PORT_STATUS


def test_rust_catalog_ids_are_marked_rust_backed() -> None:
    if not rust_catalog_available():
        pytest.skip("ta_py metadata endpoints are unavailable in this environment")
    rust_catalog = list_catalog_metadata(source="rust")
    non_rust: list[str] = []
    for indicator_id in rust_catalog:
        status = INDICATOR_PORT_STATUS.get(indicator_id)
        if status not in {"rust_native", "rust_via_primitives"}:
            non_rust.append(indicator_id)
    assert not non_rust, f"Rust catalog ids must be marked rust-backed in matrix: {sorted(non_rust)}"


def test_python_compute_backlog_is_explicit() -> None:
    # Rust-first target state: no public indicators should remain Python-compute owned.
    backlog = sorted(k for k, v in INDICATOR_PORT_STATUS.items() if v == "python_compute")
    assert not backlog, f"Rust-first ownership violated; remaining python_compute indicators: {backlog}"
