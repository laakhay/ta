from __future__ import annotations

import pytest

from laakhay.ta.catalog import list_catalog, list_catalog_metadata
from laakhay.ta.catalog.rust_catalog import rust_catalog_available


def _pick_shared_fields(meta: dict) -> dict:
    param_names = tuple(p.get("name") for p in meta.get("params", ()) if p.get("name") != "return_mode")
    return {
        "id": meta["id"],
        "params": param_names,
        "outputs": tuple(o.get("name") for o in meta.get("outputs", ())),
        "required_fields": tuple(meta.get("semantics", {}).get("required_fields", ())),
    }


def test_rust_catalog_entries_exist_in_python_catalog() -> None:
    if not rust_catalog_available():
        pytest.skip("ta_py metadata endpoints are unavailable in this environment")
    rust_catalog = list_catalog_metadata(source="rust")
    python_catalog = list_catalog_metadata(source="python")
    public_ids = set(list_catalog().keys())

    missing = sorted((set(rust_catalog) & public_ids) - set(python_catalog))
    assert not missing, f"Rust catalog entries missing from Python catalog: {missing}"


def test_rust_python_metadata_parity_for_shared_ids() -> None:
    if not rust_catalog_available():
        pytest.skip("ta_py metadata endpoints are unavailable in this environment")
    rust_catalog = list_catalog_metadata(source="rust")
    python_catalog = list_catalog_metadata(source="python")
    public_ids = set(list_catalog().keys())

    shared = sorted((set(rust_catalog).intersection(python_catalog)).intersection(public_ids))
    assert shared, "Expected at least one shared indicator id between Rust and Python catalogs"

    mismatches: list[str] = []
    for indicator_id in shared:
        rust_view = _pick_shared_fields(rust_catalog[indicator_id])
        py_view = _pick_shared_fields(python_catalog[indicator_id])
        if rust_view != py_view:
            mismatches.append(indicator_id)

    assert not mismatches, f"Metadata mismatches for shared ids: {mismatches}"
