#[test]
fn abi_version_is_v1() {
    let v = ta_ffi::ta_engine_abi_version();
    assert_eq!(v, 1);
}
