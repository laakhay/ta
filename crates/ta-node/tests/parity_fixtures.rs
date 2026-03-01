use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Periods {
    short: u32,
    fast: u32,
    slow: u32,
    signal: u32,
}

#[derive(Debug, Deserialize)]
struct ParityCases {
    series: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    periods: Periods,
}

fn load_fixture() -> ParityCases {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/test/fixtures/parity_cases.json"
    );
    let content = std::fs::read_to_string(path).expect("fixture file should be readable");
    serde_json::from_str(&content).expect("fixture should be valid json")
}

fn assert_series_close(lhs: &[f64], rhs: &[f64], tol: f64) {
    assert_eq!(lhs.len(), rhs.len(), "length mismatch");
    for (i, (a, b)) in lhs.iter().zip(rhs.iter()).enumerate() {
        if a.is_nan() && b.is_nan() {
            continue;
        }
        let delta = (a - b).abs();
        assert!(delta <= tol, "index {i}: {a} vs {b} (delta={delta})");
    }
}

#[test]
fn parity_single_output_wrappers_match_engine() {
    let f = load_fixture();

    let node_sma = ta_node::sma(f.series.clone(), f.periods.short).expect("sma");
    let ref_sma = ta_engine::rolling::rolling_mean(&f.series, f.periods.short as usize);
    assert_series_close(&node_sma, &ref_sma, 1e-12);

    let node_rsi = ta_node::rsi(f.series.clone(), f.periods.short).expect("rsi");
    let ref_rsi = ta_engine::momentum::rsi(&f.series, f.periods.short as usize);
    assert_series_close(&node_rsi, &ref_rsi, 1e-12);

    let node_atr = ta_node::atr(
        f.high.clone(),
        f.low.clone(),
        f.close.clone(),
        f.periods.short,
    )
    .expect("atr");
    let ref_atr = ta_engine::volatility::atr(&f.high, &f.low, &f.close, f.periods.short as usize);
    assert_series_close(&node_atr, &ref_atr, 1e-12);

    let node_obv = ta_node::obv(f.close.clone(), f.volume.clone()).expect("obv");
    let ref_obv = ta_engine::volume::obv(&f.close, &f.volume);
    assert_series_close(&node_obv, &ref_obv, 1e-12);
}

#[test]
fn parity_multi_output_wrappers_match_engine() {
    let f = load_fixture();

    let node_macd = ta_node::macd(
        f.series.clone(),
        f.periods.fast,
        f.periods.slow,
        f.periods.signal,
    )
    .expect("macd");
    let (ref_macd, ref_signal, ref_hist) = ta_engine::trend::macd(
        &f.series,
        f.periods.fast as usize,
        f.periods.slow as usize,
        f.periods.signal as usize,
    );
    assert_series_close(&node_macd.macd, &ref_macd, 1e-12);
    assert_series_close(&node_macd.signal, &ref_signal, 1e-12);
    assert_series_close(&node_macd.histogram, &ref_hist, 1e-12);

    let node_bbands = ta_node::bbands(f.series.clone(), f.periods.short, 2.0).expect("bbands");
    let (ref_upper, ref_middle, ref_lower) =
        ta_engine::volatility::bbands(&f.series, f.periods.short as usize, 2.0);
    assert_series_close(&node_bbands.upper, &ref_upper, 1e-12);
    assert_series_close(&node_bbands.middle, &ref_middle, 1e-12);
    assert_series_close(&node_bbands.lower, &ref_lower, 1e-12);

    let node_adx = ta_node::adx(
        f.high.clone(),
        f.low.clone(),
        f.close.clone(),
        f.periods.short,
    )
    .expect("adx");
    let (ref_adx, ref_plus_di, ref_minus_di) =
        ta_engine::trend::adx(&f.high, &f.low, &f.close, f.periods.short as usize);
    assert_series_close(&node_adx.adx, &ref_adx, 1e-12);
    assert_series_close(&node_adx.plus_di, &ref_plus_di, 1e-12);
    assert_series_close(&node_adx.minus_di, &ref_minus_di, 1e-12);
}
