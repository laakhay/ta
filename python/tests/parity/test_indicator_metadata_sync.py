from __future__ import annotations

import pytest

from laakhay.ta.catalog import describe_indicator, list_catalog, list_catalog_metadata
from laakhay.ta.catalog.rust_catalog import rust_catalog_available


def _pick_shared_fields(meta: dict) -> dict:
    param_names = tuple(p.get("name") for p in meta.get("params", ()) if p.get("name") != "return_mode")
    visual = meta.get("visual", {}) or {}
    output_visual_map = {
        str(v.get("output")): str(v.get("primitive"))
        for v in visual.get("output_visuals", ())
        if "|" not in str(v.get("output", ""))
    }
    return {
        "id": meta["id"],
        "params": param_names,
        "outputs": tuple(o.get("name") for o in meta.get("outputs", ())),
        "pane_hint": visual.get("pane_hint"),
        "scale_group": visual.get("scale_group"),
        "output_visual_map": output_visual_map,
    }


def _pick_python_descriptor_fields(indicator_id: str) -> dict:
    descriptor = describe_indicator(indicator_id)
    output_visual_map = {
        output.name: str((output.metadata or {}).get("visual", {}).get("primitive", ""))
        for output in descriptor.outputs
    }
    return {
        "id": indicator_id,
        "params": tuple(param.name for param in descriptor.parameters if param.name != "return_mode"),
        "outputs": tuple(output.name for output in descriptor.outputs),
        "pane_hint": list_catalog_metadata()[indicator_id].get("visual", {}).get("pane_hint"),
        "scale_group": list_catalog_metadata()[indicator_id].get("visual", {}).get("scale_group"),
        "output_visual_map": output_visual_map,
    }


def test_rust_python_registry_parity_for_public_ids() -> None:
    if not rust_catalog_available():
        pytest.skip("ta_py metadata endpoints are unavailable in this environment")
    rust_catalog = list_catalog_metadata()
    public_ids = set(list_catalog().keys())

    shared = sorted(set(rust_catalog).intersection(public_ids))
    assert shared, "Expected at least one shared indicator id between Rust and Python catalogs"

    mismatches: list[str] = []
    for indicator_id in shared:
        rust_view = _pick_shared_fields(rust_catalog[indicator_id])
        py_view = _pick_python_descriptor_fields(indicator_id)
        if rust_view != py_view:
            mismatches.append(indicator_id)

    assert not mismatches, f"Rust metadata mismatches against Python descriptor surface for ids: {mismatches}"
