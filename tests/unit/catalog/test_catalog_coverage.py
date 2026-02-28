from __future__ import annotations

from laakhay.ta.catalog import list_catalog
from laakhay.ta.catalog.porting_matrix import INDICATOR_PORT_STATUS


def test_porting_matrix_covers_full_catalog_surface() -> None:
    catalog_ids = set(list_catalog().keys())
    matrix_ids = set(INDICATOR_PORT_STATUS.keys())

    missing = sorted(catalog_ids - matrix_ids)
    extra = sorted(matrix_ids - catalog_ids)
    assert not missing, f"Missing indicators in porting matrix: {missing}"
    assert not extra, f"Extra indicators in porting matrix: {extra}"


def test_porting_matrix_uses_known_status_values() -> None:
    allowed = {"rust_native", "rust_via_primitives", "python_compute", "blocked"}
    unknown = sorted({status for status in INDICATOR_PORT_STATUS.values() if status not in allowed})
    assert not unknown, f"Unknown port status values found: {unknown}"
