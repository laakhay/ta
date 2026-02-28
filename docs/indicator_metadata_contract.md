# Indicator Metadata Contract (Rust Canonical)

Contract owner: `rust/crates/ta-engine/src/metadata.rs`

Python access points:
- `ta_py.indicator_catalog() -> list[dict]`
- `ta_py.indicator_meta(id: str) -> dict`
- `laakhay.ta.catalog.list_catalog_metadata(source="rust") -> dict[str, dict]`

## Entry Shape

Each indicator metadata entry uses the following fields:

```json
{
  "id": "rsi",
  "display_name": "Relative Strength Index",
  "category": "momentum",
  "runtime_binding": "rsi",
  "aliases": ["..."],
  "param_aliases": {"lookback": "period"},
  "params": [
    {
      "name": "period",
      "kind": "int",
      "required": false,
      "default": "14",
      "description": "Lookback period",
      "min": 1.0,
      "max": null
    }
  ],
  "outputs": [
    {
      "name": "result",
      "kind": "line",
      "description": "RSI value"
    }
  ],
  "semantics": {
    "required_fields": ["close"],
    "optional_fields": [],
    "lookback_params": ["period"],
    "default_lookback": null,
    "warmup_policy": "window"
  }
}
```

## Stability Rules

1. Rust metadata is canonical for shared fields.
2. Python metadata extensions may add optional fields but cannot redefine shared field semantics.
3. Breaking shape changes require:
- contract doc update,
- snapshot/test updates,
- version bump in release notes.
