//! C ABI surface for ta-engine.

#[unsafe(no_mangle)]
pub extern "C" fn ta_engine_abi_version() -> u32 {
    1
}
