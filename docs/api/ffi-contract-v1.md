# FFI Contract v1

Status: active

Library:
- crate: `ta-ffi`
- header: `rust/crates/ta-ffi/include/ta_engine.h`

ABI version:
- `ta_engine_abi_version()` returns `1`

Error/status model:
- `TA_STATUS_OK = 0`
- `TA_STATUS_INVALID_INPUT = 1`
- `TA_STATUS_SHAPE_MISMATCH = 2`
- `TA_STATUS_INTERNAL_ERROR = 255`

Compatibility policy (beta):
- ABI version bump is required for any breaking symbol/signature change.
- Non-breaking additions may be introduced under the same ABI version.
