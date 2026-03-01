use napi_derive::napi;

fn validate_period(period: u32) -> napi::Result<usize> {
    if period == 0 {
        return Err(napi::Error::from_reason(
            "ERR_PERIOD_INVALID: period must be > 0",
        ));
    }
    Ok(period as usize)
}

#[napi(object)]
pub struct MacdOutput {
    pub macd: Vec<f64>,
    pub signal: Vec<f64>,
    pub histogram: Vec<f64>,
}

#[napi(object)]
pub struct BbandsOutput {
    pub upper: Vec<f64>,
    pub middle: Vec<f64>,
    pub lower: Vec<f64>,
}

#[napi]
pub fn engine_version() -> String {
    ta_engine::engine_version().to_string()
}

#[napi]
pub fn sma(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = validate_period(period)?;
    Ok(ta_engine::rolling::rolling_mean(&values, period))
}

#[napi]
pub fn ema(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = validate_period(period)?;
    Ok(ta_engine::moving_averages::ema(&values, period))
}

#[napi]
pub fn wma(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = validate_period(period)?;
    Ok(ta_engine::moving_averages::wma(&values, period))
}

#[napi]
pub fn hma(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = validate_period(period)?;
    Ok(ta_engine::moving_averages::hma(&values, period))
}

#[napi]
pub fn rsi(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = validate_period(period)?;
    Ok(ta_engine::momentum::rsi(&values, period))
}

#[napi]
pub fn roc(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = validate_period(period)?;
    Ok(ta_engine::momentum::roc(&values, period))
}

#[napi]
pub fn cmo(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = validate_period(period)?;
    Ok(ta_engine::momentum::cmo(&values, period))
}

#[napi]
pub fn macd(
    values: Vec<f64>,
    fast_period: u32,
    slow_period: u32,
    signal_period: u32,
) -> napi::Result<MacdOutput> {
    let fast_period = validate_period(fast_period)?;
    let slow_period = validate_period(slow_period)?;
    let signal_period = validate_period(signal_period)?;
    let (macd, signal, histogram) =
        ta_engine::trend::macd(&values, fast_period, slow_period, signal_period);
    Ok(MacdOutput {
        macd,
        signal,
        histogram,
    })
}

#[napi]
pub fn bbands(values: Vec<f64>, period: u32, std_dev: f64) -> napi::Result<BbandsOutput> {
    let period = validate_period(period)?;
    let (upper, middle, lower) = ta_engine::volatility::bbands(&values, period, std_dev);
    Ok(BbandsOutput {
        upper,
        middle,
        lower,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn engine_version_is_exposed() {
        assert_eq!(engine_version(), "0.1.0".to_string());
    }

    #[test]
    fn sma_validates_period() {
        let err = sma(vec![1.0, 2.0, 3.0], 0).expect_err("period=0 must fail");
        assert!(err.to_string().contains("ERR_PERIOD_INVALID"));
    }

    #[test]
    fn direct_indicators_return_series_with_input_length() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        assert_eq!(
            sma(values.clone(), 2).expect("sma should succeed").len(),
            values.len()
        );
        assert_eq!(
            ema(values.clone(), 2).expect("ema should succeed").len(),
            values.len()
        );
        assert_eq!(
            wma(values.clone(), 2).expect("wma should succeed").len(),
            values.len()
        );
        assert_eq!(
            hma(values.clone(), 2).expect("hma should succeed").len(),
            values.len()
        );
        assert_eq!(
            rsi(values.clone(), 2).expect("rsi should succeed").len(),
            values.len()
        );
        assert_eq!(
            roc(values.clone(), 2).expect("roc should succeed").len(),
            values.len()
        );
        assert_eq!(
            cmo(values.clone(), 2).expect("cmo should succeed").len(),
            values.len()
        );
    }

    #[test]
    fn multi_output_indicators_have_consistent_lengths() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0];
        let macd_out = macd(values.clone(), 2, 3, 2).expect("macd should succeed");
        assert_eq!(macd_out.macd.len(), values.len());
        assert_eq!(macd_out.signal.len(), values.len());
        assert_eq!(macd_out.histogram.len(), values.len());

        let bb = bbands(values.clone(), 2, 2.0).expect("bbands should succeed");
        assert_eq!(bb.upper.len(), values.len());
        assert_eq!(bb.middle.len(), values.len());
        assert_eq!(bb.lower.len(), values.len());
    }
}
