use pyo3::prelude::*;

use crate::conversions::IchimokuTuple;

fn validate_period(period: usize) -> PyResult<()> {
    if period == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "period must be positive",
        ));
    }
    Ok(())
}

#[pyfunction]
pub(crate) fn rolling_sum(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_sum(&values, period))
}
#[pyfunction]
pub(crate) fn rolling_mean(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_mean(&values, period))
}
#[pyfunction]
pub(crate) fn rolling_std(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_std(&values, period))
}
#[pyfunction]
pub(crate) fn rolling_min(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_min(&values, period))
}
#[pyfunction]
pub(crate) fn rolling_max(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_max(&values, period))
}
#[pyfunction]
pub(crate) fn rolling_ema(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::ema(&values, period))
}
#[pyfunction]
pub(crate) fn rolling_rma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::rma(&values, period))
}
#[pyfunction]
pub(crate) fn rolling_wma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::wma(&values, period))
}
#[pyfunction]
pub(crate) fn hma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::hma(&values, period))
}
#[pyfunction]
pub(crate) fn rsi(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::rsi(&values, period))
}
#[pyfunction]
pub(crate) fn roc(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::roc(&values, period))
}
#[pyfunction]
pub(crate) fn cmo(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::cmo(&values, period))
}
#[pyfunction]
pub(crate) fn ao(
    high: Vec<f64>,
    low: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(fast_period)?;
    validate_period(slow_period)?;
    Ok(ta_engine::momentum::ao(
        &high,
        &low,
        fast_period,
        slow_period,
    ))
}
#[pyfunction]
pub(crate) fn coppock(
    values: Vec<f64>,
    wma_period: usize,
    fast_roc: usize,
    slow_roc: usize,
) -> PyResult<Vec<f64>> {
    validate_period(wma_period)?;
    validate_period(fast_roc)?;
    validate_period(slow_roc)?;
    Ok(ta_engine::momentum::coppock(
        &values, wma_period, fast_roc, slow_roc,
    ))
}
#[pyfunction]
pub(crate) fn mfi(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::mfi(
        &high, &low, &close, &volume, period,
    ))
}
#[pyfunction]
pub(crate) fn vortex(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::momentum::vortex(&high, &low, &close, period))
}
#[pyfunction]
pub(crate) fn atr(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volatility::atr(&high, &low, &close, period))
}
#[pyfunction]
pub(crate) fn atr_from_tr(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volatility::atr_from_tr(&values, period))
}
#[pyfunction]
pub(crate) fn stochastic_kd(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    k_period: usize,
    d_period: usize,
    smooth: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(k_period)?;
    validate_period(d_period)?;
    validate_period(smooth)?;
    Ok(ta_engine::momentum::stochastic_kd(
        &high, &low, &close, k_period, d_period, smooth,
    ))
}
#[pyfunction]
pub(crate) fn obv(close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::obv(&close, &volume))
}
#[pyfunction]
pub(crate) fn macd(
    values: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(fast_period)?;
    validate_period(slow_period)?;
    validate_period(signal_period)?;
    Ok(ta_engine::trend::macd(
        &values,
        fast_period,
        slow_period,
        signal_period,
    ))
}
#[pyfunction]
pub(crate) fn bbands(
    values: Vec<f64>,
    period: usize,
    std_dev: f64,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::volatility::bbands(&values, period, std_dev))
}
#[pyfunction]
pub(crate) fn donchian(
    high: Vec<f64>,
    low: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::volatility::donchian(&high, &low, period))
}
#[pyfunction]
pub(crate) fn keltner(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    ema_period: usize,
    atr_period: usize,
    multiplier: f64,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(ema_period)?;
    validate_period(atr_period)?;
    Ok(ta_engine::volatility::keltner(
        &high, &low, &close, ema_period, atr_period, multiplier,
    ))
}
#[pyfunction]
pub(crate) fn ichimoku(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tenkan_period: usize,
    kijun_period: usize,
    span_b_period: usize,
    displacement: usize,
) -> PyResult<IchimokuTuple> {
    validate_period(tenkan_period)?;
    validate_period(kijun_period)?;
    validate_period(span_b_period)?;
    validate_period(displacement)?;
    Ok(ta_engine::trend::ichimoku(
        &high,
        &low,
        &close,
        tenkan_period,
        kijun_period,
        span_b_period,
        displacement,
    ))
}
#[pyfunction]
pub(crate) fn fisher(
    high: Vec<f64>,
    low: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::fisher(&high, &low, period))
}
#[pyfunction]
pub(crate) fn psar(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    af_start: f64,
    af_increment: f64,
    af_max: f64,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    Ok(ta_engine::trend::psar(
        &high,
        &low,
        &close,
        af_start,
        af_increment,
        af_max,
    ))
}
#[pyfunction]
pub(crate) fn supertrend(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
    multiplier: f64,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::supertrend(
        &high, &low, &close, period, multiplier,
    ))
}
#[pyfunction]
pub(crate) fn adx(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::adx(&high, &low, &close, period))
}
#[pyfunction]
pub(crate) fn swing_points_raw(
    high: Vec<f64>,
    low: Vec<f64>,
    left: usize,
    right: usize,
    allow_equal_extremes: bool,
) -> PyResult<(Vec<bool>, Vec<bool>)> {
    Ok(ta_engine::trend::swing_points_raw(
        &high,
        &low,
        left,
        right,
        allow_equal_extremes,
    ))
}
#[pyfunction]
pub(crate) fn cci(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    Ok(ta_engine::momentum::cci(&high, &low, &close, period))
}
#[pyfunction]
pub(crate) fn elder_ray(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(period)?;
    Ok(ta_engine::trend::elder_ray(&high, &low, &close, period))
}
#[pyfunction]
pub(crate) fn williams_r(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::williams_r(&high, &low, &close, period))
}
#[pyfunction]
pub(crate) fn crossup(a: Vec<f64>, b: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::crossup(&a, &b))
}
#[pyfunction]
pub(crate) fn crossdown(a: Vec<f64>, b: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::crossdown(&a, &b))
}
#[pyfunction]
pub(crate) fn cross(a: Vec<f64>, b: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::cross(&a, &b))
}
#[pyfunction]
pub(crate) fn rising(a: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::rising(&a))
}
#[pyfunction]
pub(crate) fn falling(a: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::falling(&a))
}
#[pyfunction]
pub(crate) fn rising_pct(a: Vec<f64>, pct: f64) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::rising_pct(&a, pct))
}
#[pyfunction]
pub(crate) fn falling_pct(a: Vec<f64>, pct: f64) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::falling_pct(&a, pct))
}
#[pyfunction]
pub(crate) fn in_channel(price: Vec<f64>, upper: Vec<f64>, lower: Vec<f64>) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::in_channel(&price, &upper, &lower))
}
#[pyfunction]
pub(crate) fn out_channel(
    price: Vec<f64>,
    upper: Vec<f64>,
    lower: Vec<f64>,
) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::out_channel(&price, &upper, &lower))
}
#[pyfunction]
pub(crate) fn enter_channel(
    price: Vec<f64>,
    upper: Vec<f64>,
    lower: Vec<f64>,
) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::enter_channel(&price, &upper, &lower))
}
#[pyfunction]
pub(crate) fn exit_channel(
    price: Vec<f64>,
    upper: Vec<f64>,
    lower: Vec<f64>,
) -> PyResult<Vec<bool>> {
    Ok(ta_engine::events::exit_channel(&price, &upper, &lower))
}
#[pyfunction]
pub(crate) fn vwap(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::vwap(&high, &low, &close, &volume))
}
#[pyfunction]
pub(crate) fn klinger_vf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::klinger_vf(&high, &low, &close, &volume))
}
#[pyfunction]
pub(crate) fn klinger(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(fast_period)?;
    validate_period(slow_period)?;
    validate_period(signal_period)?;
    Ok(ta_engine::volume::klinger(
        &high,
        &low,
        &close,
        &volume,
        fast_period,
        slow_period,
        signal_period,
    ))
}
#[pyfunction]
pub(crate) fn cmf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volume::cmf(&high, &low, &close, &volume, period))
}
