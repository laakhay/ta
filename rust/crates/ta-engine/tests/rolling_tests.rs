use ta_engine::rolling;

#[test]
fn rolling_mean_basic() {
    let out = rolling::rolling_mean(&[1.0, 2.0, 3.0, 4.0], 3);
    assert!(out[0].is_nan());
    assert!(out[1].is_nan());
    assert_eq!(out[2], 2.0);
    assert_eq!(out[3], 3.0);
}

#[test]
fn rolling_min_max_basic() {
    let min_out = rolling::rolling_min(&[5.0, 3.0, 4.0, 2.0], 2);
    let max_out = rolling::rolling_max(&[5.0, 3.0, 4.0, 2.0], 2);

    assert!(min_out[0].is_nan());
    assert_eq!(min_out[1], 3.0);
    assert_eq!(min_out[2], 3.0);
    assert_eq!(min_out[3], 2.0);

    assert!(max_out[0].is_nan());
    assert_eq!(max_out[1], 5.0);
    assert_eq!(max_out[2], 4.0);
    assert_eq!(max_out[3], 4.0);
}
