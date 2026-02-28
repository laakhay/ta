"""Rust catalog bridge helpers.

This module provides a lightweight adapter over `ta_py.indicator_catalog()`
so Python APIs can consume Rust-owned indicator metadata without coupling to
registry internals.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _load_ta_py() -> Any:
    import ta_py

    return ta_py


def rust_catalog_available() -> bool:
    """Return True when ta_py exposes metadata endpoints."""
    try:
        ta_py = _load_ta_py()
    except Exception:
        return False
    return hasattr(ta_py, "indicator_catalog") and hasattr(ta_py, "indicator_meta")


def _normalize_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a single Rust metadata entry to deterministic Python shapes."""
    aliases = tuple(str(a) for a in entry.get("aliases", []))
    params = tuple(
        {
            "name": str(p.get("name", "")),
            "kind": str(p.get("kind", "unknown")),
            "required": bool(p.get("required", False)),
            "default": p.get("default"),
            "description": str(p.get("description", "")),
            "min": p.get("min"),
            "max": p.get("max"),
        }
        for p in entry.get("params", [])
    )
    outputs = tuple(
        {
            "name": str(o.get("name", "")),
            "kind": str(o.get("kind", "line")),
            "description": str(o.get("description", "")),
        }
        for o in entry.get("outputs", [])
    )
    semantics_raw = entry.get("semantics", {}) or {}
    semantics = {
        "required_fields": tuple(str(v) for v in semantics_raw.get("required_fields", [])),
        "optional_fields": tuple(str(v) for v in semantics_raw.get("optional_fields", [])),
        "lookback_params": tuple(str(v) for v in semantics_raw.get("lookback_params", [])),
        "default_lookback": semantics_raw.get("default_lookback"),
        "warmup_policy": str(semantics_raw.get("warmup_policy", "")),
    }
    return {
        "id": str(entry.get("id", "")),
        "display_name": str(entry.get("display_name", "")),
        "category": str(entry.get("category", "custom")),
        "runtime_binding": str(entry.get("runtime_binding", "")),
        "aliases": aliases,
        "param_aliases": dict(entry.get("param_aliases", {}) or {}),
        "params": params,
        "outputs": outputs,
        "semantics": semantics,
        "source": "rust",
    }


def list_rust_catalog() -> dict[str, dict[str, Any]]:
    """Return Rust indicator metadata keyed by canonical id."""
    ta_py = _load_ta_py()
    raw = ta_py.indicator_catalog()
    out: dict[str, dict[str, Any]] = {}
    for item in raw:
        normalized = _normalize_entry(item)
        out[normalized["id"]] = normalized
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def get_rust_indicator_meta(indicator_id: str) -> dict[str, Any]:
    """Get a single Rust indicator metadata entry by id or alias."""
    ta_py = _load_ta_py()
    return _normalize_entry(ta_py.indicator_meta(indicator_id))
