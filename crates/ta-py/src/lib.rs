use pyo3::prelude::*;

mod api;
mod conversions;
mod errors;
mod state;

#[pymodule]
fn ta_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(api::dataset::engine_version, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::dataset_create, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::dataset_drop, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::dataset_append_ohlcv, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::dataset_append_series, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::dataset_info, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::series_downsample, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::series_upsample_ffill, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::series_sync_timeframe, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::indicator_catalog, m)?)?;
    m.add_function(wrap_pyfunction!(api::dataset::indicator_meta, m)?)?;

    m.add_function(wrap_pyfunction!(api::indicators::rolling_sum, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rolling_mean, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rolling_std, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rolling_min, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rolling_max, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rolling_ema, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rolling_rma, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rolling_wma, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rsi, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::roc, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::cmo, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::ao, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::coppock, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::mfi, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::vortex, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::atr, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::atr_from_tr, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::stochastic_kd, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::macd, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::bbands, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::donchian, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::keltner, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::ichimoku, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::fisher, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::psar, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::supertrend, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::adx, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::swing_points_raw, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::cci, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::williams_r, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::elder_ray, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::crossup, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::crossdown, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::cross, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rising, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::falling, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::rising_pct, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::falling_pct, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::in_channel, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::out_channel, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::enter_channel, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::exit_channel, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::vwap, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::obv, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::klinger_vf, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::klinger, m)?)?;
    m.add_function(wrap_pyfunction!(api::indicators::cmf, m)?)?;

    m.add_function(wrap_pyfunction!(api::execution::incremental_initialize, m)?)?;
    m.add_function(wrap_pyfunction!(api::execution::incremental_step, m)?)?;
    m.add_function(wrap_pyfunction!(api::execution::incremental_snapshot, m)?)?;
    m.add_function(wrap_pyfunction!(api::execution::incremental_replay, m)?)?;
    m.add_function(wrap_pyfunction!(api::execution::execute_plan, m)?)?;
    m.add_function(wrap_pyfunction!(api::execution::execute_plan_payload, m)?)?;
    Ok(())
}
