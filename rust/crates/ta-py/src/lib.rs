use pyo3::prelude::*;

#[pyfunction]
fn engine_version() -> &'static str {
    ta_engine::engine_version()
}

fn validate_period(period: usize) -> PyResult<()> {
    if period == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "period must be positive",
        ));
    }
    Ok(())
}

#[pyfunction]
fn rolling_sum(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_sum(&values, period))
}

#[pyfunction]
fn rolling_mean(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_mean(&values, period))
}

#[pyfunction]
fn rolling_std(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_std(&values, period))
}

#[pyfunction]
fn rolling_min(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_min(&values, period))
}

#[pyfunction]
fn rolling_max(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::rolling::rolling_max(&values, period))
}

#[pyfunction]
fn rolling_ema(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::ema(&values, period))
}

#[pyfunction]
fn rolling_rma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::rma(&values, period))
}

#[pyfunction]
fn rolling_wma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::moving_averages::wma(&values, period))
}

#[pyfunction]
fn rsi(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::momentum::rsi(&values, period))
}

#[pyfunction]
fn atr_from_tr(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volatility::atr_from_tr(&values, period))
}

#[pyfunction]
fn stochastic_kd(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    k_period: usize,
    d_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    validate_period(k_period)?;
    validate_period(d_period)?;
    Ok(ta_engine::momentum::stochastic_kd(
        &high, &low, &close, k_period, d_period,
    ))
}

#[pyfunction]
fn obv(close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::obv(&close, &volume))
}

#[pyfunction]
fn klinger_vf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(ta_engine::volume::klinger_vf(&high, &low, &close, &volume))
}

#[pyfunction]
fn cmf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    validate_period(period)?;
    Ok(ta_engine::volume::cmf(&high, &low, &close, &volume, period))
}

#[pymodule]
fn ta_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(engine_version, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_sum, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_mean, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_std, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_min, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_max, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_ema, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_rma, m)?)?;
    m.add_function(wrap_pyfunction!(rolling_wma, m)?)?;
    m.add_function(wrap_pyfunction!(rsi, m)?)?;
    m.add_function(wrap_pyfunction!(atr_from_tr, m)?)?;
    m.add_function(wrap_pyfunction!(stochastic_kd, m)?)?;
    m.add_function(wrap_pyfunction!(obv, m)?)?;
    m.add_function(wrap_pyfunction!(klinger_vf, m)?)?;
    m.add_function(wrap_pyfunction!(cmf, m)?)?;
    Ok(())
}
