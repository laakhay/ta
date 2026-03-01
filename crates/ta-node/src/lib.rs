use napi_derive::napi;

fn period_from_u32(period: u32) -> napi::Result<usize> {
    if period == 0 {
        return Err(napi::Error::from_reason(
            "ERR_PERIOD_INVALID: period must be > 0",
        ));
    }
    Ok(period as usize)
}

fn ensure_same_len(label: &str, lengths: &[usize]) -> napi::Result<()> {
    if lengths.is_empty() {
        return Ok(());
    }
    let first = lengths[0];
    if lengths.iter().all(|len| *len == first) {
        return Ok(());
    }
    Err(napi::Error::from_reason(format!(
        "ERR_LENGTH_MISMATCH: {label} inputs must have identical lengths"
    )))
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

#[napi(object)]
pub struct StochasticOutput {
    pub k: Vec<f64>,
    pub d: Vec<f64>,
}

#[napi(object)]
pub struct AdxOutput {
    pub adx: Vec<f64>,
    pub plus_di: Vec<f64>,
    pub minus_di: Vec<f64>,
}

#[napi(object)]
pub struct IchimokuOutput {
    pub tenkan_sen: Vec<f64>,
    pub kijun_sen: Vec<f64>,
    pub senkou_span_a: Vec<f64>,
    pub senkou_span_b: Vec<f64>,
    pub chikou_span: Vec<f64>,
}

#[napi(object)]
pub struct SupertrendOutput {
    pub supertrend: Vec<f64>,
    pub direction: Vec<f64>,
}

#[napi(object)]
pub struct PsarOutput {
    pub sar: Vec<f64>,
    pub direction: Vec<f64>,
}

#[napi(object)]
pub struct SwingPointsOutput {
    pub swing_high: Vec<bool>,
    pub swing_low: Vec<bool>,
}

#[napi(object)]
pub struct VortexOutput {
    pub plus: Vec<f64>,
    pub minus: Vec<f64>,
}

#[napi(object)]
pub struct ElderRayOutput {
    pub bull: Vec<f64>,
    pub bear: Vec<f64>,
}

#[napi(object)]
pub struct FisherOutput {
    pub fisher: Vec<f64>,
    pub signal: Vec<f64>,
}

#[napi(object)]
pub struct DonchianOutput {
    pub upper: Vec<f64>,
    pub lower: Vec<f64>,
    pub middle: Vec<f64>,
}

#[napi(object)]
pub struct KeltnerOutput {
    pub upper: Vec<f64>,
    pub middle: Vec<f64>,
    pub lower: Vec<f64>,
}

#[napi(object)]
pub struct KlingerOutput {
    pub klinger: Vec<f64>,
    pub signal: Vec<f64>,
}

#[napi]
pub fn engine_version() -> String {
    ta_engine::engine_version().to_string()
}

#[napi]
pub fn sma(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::rolling::rolling_mean(&values, period))
}

#[napi]
pub fn ema(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::moving_averages::ema(&values, period))
}

#[napi]
pub fn rma(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::moving_averages::rma(&values, period))
}

#[napi]
pub fn wma(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::moving_averages::wma(&values, period))
}

#[napi]
pub fn hma(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::moving_averages::hma(&values, period))
}

#[napi]
pub fn rsi(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::momentum::rsi(&values, period))
}

#[napi]
pub fn roc(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::momentum::roc(&values, period))
}

#[napi]
pub fn cmo(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::momentum::cmo(&values, period))
}

#[napi]
pub fn ao(
    high: Vec<f64>,
    low: Vec<f64>,
    fast_period: u32,
    slow_period: u32,
) -> napi::Result<Vec<f64>> {
    ensure_same_len("ao", &[high.len(), low.len()])?;
    let fast_period = period_from_u32(fast_period)?;
    let slow_period = period_from_u32(slow_period)?;
    Ok(ta_engine::momentum::ao(
        &high,
        &low,
        fast_period,
        slow_period,
    ))
}

#[napi]
pub fn coppock(
    values: Vec<f64>,
    wma_period: u32,
    fast_roc: u32,
    slow_roc: u32,
) -> napi::Result<Vec<f64>> {
    let wma_period = period_from_u32(wma_period)?;
    let fast_roc = period_from_u32(fast_roc)?;
    let slow_roc = period_from_u32(slow_roc)?;
    Ok(ta_engine::momentum::coppock(
        &values, wma_period, fast_roc, slow_roc,
    ))
}

#[napi]
pub fn williams_r(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: u32,
) -> napi::Result<Vec<f64>> {
    ensure_same_len("williams_r", &[high.len(), low.len(), close.len()])?;
    let period = period_from_u32(period)?;
    Ok(ta_engine::momentum::williams_r(&high, &low, &close, period))
}

#[napi]
pub fn mfi(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: u32,
) -> napi::Result<Vec<f64>> {
    ensure_same_len("mfi", &[high.len(), low.len(), close.len(), volume.len()])?;
    let period = period_from_u32(period)?;
    Ok(ta_engine::momentum::mfi(
        &high, &low, &close, &volume, period,
    ))
}

#[napi]
pub fn cci(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    ensure_same_len("cci", &[high.len(), low.len(), close.len()])?;
    let period = period_from_u32(period)?;
    Ok(ta_engine::momentum::cci(&high, &low, &close, period))
}

#[napi]
pub fn atr(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    ensure_same_len("atr", &[high.len(), low.len(), close.len()])?;
    let period = period_from_u32(period)?;
    Ok(ta_engine::volatility::atr(&high, &low, &close, period))
}

#[napi]
pub fn atr_from_tr(values: Vec<f64>, period: u32) -> napi::Result<Vec<f64>> {
    let period = period_from_u32(period)?;
    Ok(ta_engine::volatility::atr_from_tr(&values, period))
}

#[napi]
pub fn obv(close: Vec<f64>, volume: Vec<f64>) -> napi::Result<Vec<f64>> {
    ensure_same_len("obv", &[close.len(), volume.len()])?;
    Ok(ta_engine::volume::obv(&close, &volume))
}

#[napi]
pub fn vwap(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
) -> napi::Result<Vec<f64>> {
    ensure_same_len("vwap", &[high.len(), low.len(), close.len(), volume.len()])?;
    Ok(ta_engine::volume::vwap(&high, &low, &close, &volume))
}

#[napi]
pub fn cmf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: u32,
) -> napi::Result<Vec<f64>> {
    ensure_same_len("cmf", &[high.len(), low.len(), close.len(), volume.len()])?;
    let period = period_from_u32(period)?;
    Ok(ta_engine::volume::cmf(&high, &low, &close, &volume, period))
}

#[napi]
pub fn klinger_vf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
) -> napi::Result<Vec<f64>> {
    ensure_same_len(
        "klinger_vf",
        &[high.len(), low.len(), close.len(), volume.len()],
    )?;
    Ok(ta_engine::volume::klinger_vf(&high, &low, &close, &volume))
}

#[napi]
pub fn macd(
    values: Vec<f64>,
    fast_period: u32,
    slow_period: u32,
    signal_period: u32,
) -> napi::Result<MacdOutput> {
    let fast_period = period_from_u32(fast_period)?;
    let slow_period = period_from_u32(slow_period)?;
    let signal_period = period_from_u32(signal_period)?;
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
    let period = period_from_u32(period)?;
    let (upper, middle, lower) = ta_engine::volatility::bbands(&values, period, std_dev);
    Ok(BbandsOutput {
        upper,
        middle,
        lower,
    })
}

#[napi]
pub fn stochastic(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    k_period: u32,
    d_period: u32,
    smooth: u32,
) -> napi::Result<StochasticOutput> {
    ensure_same_len("stochastic", &[high.len(), low.len(), close.len()])?;
    let k_period = period_from_u32(k_period)?;
    let d_period = period_from_u32(d_period)?;
    let smooth = period_from_u32(smooth)?;
    let (k, d) =
        ta_engine::momentum::stochastic_kd(&high, &low, &close, k_period, d_period, smooth);
    Ok(StochasticOutput { k, d })
}

#[napi]
pub fn adx(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, period: u32) -> napi::Result<AdxOutput> {
    ensure_same_len("adx", &[high.len(), low.len(), close.len()])?;
    let period = period_from_u32(period)?;
    let (adx, plus_di, minus_di) = ta_engine::trend::adx(&high, &low, &close, period);
    Ok(AdxOutput {
        adx,
        plus_di,
        minus_di,
    })
}

#[napi]
#[allow(clippy::too_many_arguments)]
pub fn ichimoku(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tenkan_period: u32,
    kijun_period: u32,
    span_b_period: u32,
    displacement: u32,
) -> napi::Result<IchimokuOutput> {
    ensure_same_len("ichimoku", &[high.len(), low.len(), close.len()])?;
    let tenkan_period = period_from_u32(tenkan_period)?;
    let kijun_period = period_from_u32(kijun_period)?;
    let span_b_period = period_from_u32(span_b_period)?;
    let displacement = period_from_u32(displacement)?;
    let (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span) =
        ta_engine::trend::ichimoku(
            &high,
            &low,
            &close,
            tenkan_period,
            kijun_period,
            span_b_period,
            displacement,
        );
    Ok(IchimokuOutput {
        tenkan_sen,
        kijun_sen,
        senkou_span_a,
        senkou_span_b,
        chikou_span,
    })
}

#[napi]
pub fn supertrend(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: u32,
    multiplier: f64,
) -> napi::Result<SupertrendOutput> {
    ensure_same_len("supertrend", &[high.len(), low.len(), close.len()])?;
    let period = period_from_u32(period)?;
    let (supertrend, direction) =
        ta_engine::trend::supertrend(&high, &low, &close, period, multiplier);
    Ok(SupertrendOutput {
        supertrend,
        direction,
    })
}

#[napi]
pub fn psar(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    af_start: f64,
    af_increment: f64,
    af_max: f64,
) -> napi::Result<PsarOutput> {
    ensure_same_len("psar", &[high.len(), low.len(), close.len()])?;
    let (sar, direction) =
        ta_engine::trend::psar(&high, &low, &close, af_start, af_increment, af_max);
    Ok(PsarOutput { sar, direction })
}

#[napi]
pub fn swing_points_raw(
    high: Vec<f64>,
    low: Vec<f64>,
    left: u32,
    right: u32,
    allow_equal_extremes: bool,
) -> napi::Result<SwingPointsOutput> {
    ensure_same_len("swing_points_raw", &[high.len(), low.len()])?;
    let left = period_from_u32(left)?;
    let right = period_from_u32(right)?;
    let (swing_high, swing_low) =
        ta_engine::trend::swing_points_raw(&high, &low, left, right, allow_equal_extremes);
    Ok(SwingPointsOutput {
        swing_high,
        swing_low,
    })
}

#[napi]
pub fn vortex(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: u32,
) -> napi::Result<VortexOutput> {
    ensure_same_len("vortex", &[high.len(), low.len(), close.len()])?;
    let period = period_from_u32(period)?;
    let (plus, minus) = ta_engine::momentum::vortex(&high, &low, &close, period);
    Ok(VortexOutput { plus, minus })
}

#[napi]
pub fn elder_ray(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: u32,
) -> napi::Result<ElderRayOutput> {
    ensure_same_len("elder_ray", &[high.len(), low.len(), close.len()])?;
    let period = period_from_u32(period)?;
    let (bull, bear) = ta_engine::trend::elder_ray(&high, &low, &close, period);
    Ok(ElderRayOutput { bull, bear })
}

#[napi]
pub fn fisher(high: Vec<f64>, low: Vec<f64>, period: u32) -> napi::Result<FisherOutput> {
    ensure_same_len("fisher", &[high.len(), low.len()])?;
    let period = period_from_u32(period)?;
    let (fisher, signal) = ta_engine::trend::fisher(&high, &low, period);
    Ok(FisherOutput { fisher, signal })
}

#[napi]
pub fn donchian(high: Vec<f64>, low: Vec<f64>, period: u32) -> napi::Result<DonchianOutput> {
    ensure_same_len("donchian", &[high.len(), low.len()])?;
    let period = period_from_u32(period)?;
    let (upper, lower, middle) = ta_engine::volatility::donchian(&high, &low, period);
    Ok(DonchianOutput {
        upper,
        lower,
        middle,
    })
}

#[napi]
pub fn keltner(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    ema_period: u32,
    atr_period: u32,
    multiplier: f64,
) -> napi::Result<KeltnerOutput> {
    ensure_same_len("keltner", &[high.len(), low.len(), close.len()])?;
    let ema_period = period_from_u32(ema_period)?;
    let atr_period = period_from_u32(atr_period)?;
    let (upper, middle, lower) =
        ta_engine::volatility::keltner(&high, &low, &close, ema_period, atr_period, multiplier);
    Ok(KeltnerOutput {
        upper,
        middle,
        lower,
    })
}

#[napi]
#[allow(clippy::too_many_arguments)]
pub fn klinger(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    fast_period: u32,
    slow_period: u32,
    signal_period: u32,
) -> napi::Result<KlingerOutput> {
    ensure_same_len(
        "klinger",
        &[high.len(), low.len(), close.len(), volume.len()],
    )?;
    let fast_period = period_from_u32(fast_period)?;
    let slow_period = period_from_u32(slow_period)?;
    let signal_period = period_from_u32(signal_period)?;
    let (klinger, signal) = ta_engine::volume::klinger(
        &high,
        &low,
        &close,
        &volume,
        fast_period,
        slow_period,
        signal_period,
    );
    Ok(KlingerOutput { klinger, signal })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_series() -> Vec<f64> {
        vec![1.0, 2.0, 3.0, 4.0, 3.5, 4.2, 5.0, 5.2, 5.8, 6.1]
    }

    fn sample_ohlcv() -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
        let high = vec![1.1, 2.2, 3.1, 4.2, 3.7, 4.5, 5.1, 5.6, 6.0, 6.3];
        let low = vec![0.9, 1.8, 2.7, 3.8, 3.2, 3.9, 4.7, 4.9, 5.4, 5.8];
        let close = vec![1.0, 2.0, 3.0, 4.0, 3.5, 4.2, 5.0, 5.2, 5.8, 6.1];
        let volume = vec![
            100.0, 120.0, 110.0, 150.0, 90.0, 180.0, 160.0, 170.0, 155.0, 165.0,
        ];
        (high, low, close, volume)
    }

    #[test]
    fn engine_version_is_exposed() {
        assert_eq!(engine_version(), "0.1.0".to_string());
    }

    #[test]
    fn period_validation_is_stable() {
        let err = sma(vec![1.0, 2.0, 3.0], 0).expect_err("period=0 must fail");
        assert!(err.to_string().contains("ERR_PERIOD_INVALID"));
    }

    #[test]
    fn length_validation_is_stable() {
        let err =
            atr(vec![1.0], vec![1.0, 2.0], vec![1.0], 2).expect_err("mismatched lengths must fail");
        assert!(err.to_string().contains("ERR_LENGTH_MISMATCH"));
    }

    #[test]
    fn single_output_indicators_preserve_input_length() {
        let values = sample_series();
        let (high, low, close, volume) = sample_ohlcv();
        assert_eq!(sma(values.clone(), 3).expect("sma").len(), values.len());
        assert_eq!(ema(values.clone(), 3).expect("ema").len(), values.len());
        assert_eq!(rma(values.clone(), 3).expect("rma").len(), values.len());
        assert_eq!(wma(values.clone(), 3).expect("wma").len(), values.len());
        assert_eq!(hma(values.clone(), 3).expect("hma").len(), values.len());
        assert_eq!(rsi(values.clone(), 3).expect("rsi").len(), values.len());
        assert_eq!(roc(values.clone(), 3).expect("roc").len(), values.len());
        assert_eq!(cmo(values.clone(), 3).expect("cmo").len(), values.len());
        assert_eq!(
            ao(high.clone(), low.clone(), 3, 5).expect("ao").len(),
            high.len()
        );
        assert_eq!(
            coppock(values.clone(), 3, 2, 4).expect("coppock").len(),
            values.len()
        );
        assert_eq!(
            williams_r(high.clone(), low.clone(), close.clone(), 3)
                .expect("williams_r")
                .len(),
            high.len()
        );
        assert_eq!(
            mfi(high.clone(), low.clone(), close.clone(), volume.clone(), 3)
                .expect("mfi")
                .len(),
            high.len()
        );
        assert_eq!(
            cci(high.clone(), low.clone(), close.clone(), 3)
                .expect("cci")
                .len(),
            high.len()
        );
        assert_eq!(
            atr(high.clone(), low.clone(), close.clone(), 3)
                .expect("atr")
                .len(),
            high.len()
        );
        assert_eq!(
            atr_from_tr(values.clone(), 3).expect("atr_from_tr").len(),
            values.len()
        );
        assert_eq!(
            obv(close.clone(), volume.clone()).expect("obv").len(),
            close.len()
        );
        assert_eq!(
            vwap(high.clone(), low.clone(), close.clone(), volume.clone())
                .expect("vwap")
                .len(),
            high.len()
        );
        assert_eq!(
            cmf(high.clone(), low.clone(), close.clone(), volume.clone(), 3)
                .expect("cmf")
                .len(),
            high.len()
        );
        assert_eq!(
            klinger_vf(high.clone(), low.clone(), close.clone(), volume.clone())
                .expect("klinger_vf")
                .len(),
            high.len()
        );
    }

    #[test]
    fn multi_output_indicators_preserve_input_length() {
        let values = sample_series();
        let (high, low, close, volume) = sample_ohlcv();

        let macd_out = macd(values.clone(), 2, 4, 2).expect("macd");
        assert_eq!(macd_out.macd.len(), values.len());
        assert_eq!(macd_out.signal.len(), values.len());
        assert_eq!(macd_out.histogram.len(), values.len());

        let bb = bbands(values.clone(), 3, 2.0).expect("bbands");
        assert_eq!(bb.upper.len(), values.len());
        assert_eq!(bb.middle.len(), values.len());
        assert_eq!(bb.lower.len(), values.len());

        let stoch =
            stochastic(high.clone(), low.clone(), close.clone(), 3, 3, 2).expect("stochastic");
        assert_eq!(stoch.k.len(), high.len());
        assert_eq!(stoch.d.len(), high.len());

        let adx_out = adx(high.clone(), low.clone(), close.clone(), 3).expect("adx");
        assert_eq!(adx_out.adx.len(), high.len());
        assert_eq!(adx_out.plus_di.len(), high.len());
        assert_eq!(adx_out.minus_di.len(), high.len());

        let ich = ichimoku(high.clone(), low.clone(), close.clone(), 3, 4, 5, 2).expect("ichimoku");
        assert_eq!(ich.tenkan_sen.len(), high.len());
        assert_eq!(ich.kijun_sen.len(), high.len());
        assert_eq!(ich.senkou_span_a.len(), high.len());
        assert_eq!(ich.senkou_span_b.len(), high.len());
        assert_eq!(ich.chikou_span.len(), high.len());

        let sup = supertrend(high.clone(), low.clone(), close.clone(), 3, 2.0).expect("supertrend");
        assert_eq!(sup.supertrend.len(), high.len());
        assert_eq!(sup.direction.len(), high.len());

        let ps = psar(high.clone(), low.clone(), close.clone(), 0.02, 0.02, 0.2).expect("psar");
        assert_eq!(ps.sar.len(), high.len());
        assert_eq!(ps.direction.len(), high.len());

        let swing =
            swing_points_raw(high.clone(), low.clone(), 2, 2, false).expect("swing_points_raw");
        assert_eq!(swing.swing_high.len(), high.len());
        assert_eq!(swing.swing_low.len(), high.len());

        let vort = vortex(high.clone(), low.clone(), close.clone(), 3).expect("vortex");
        assert_eq!(vort.plus.len(), high.len());
        assert_eq!(vort.minus.len(), high.len());

        let elder = elder_ray(high.clone(), low.clone(), close.clone(), 3).expect("elder_ray");
        assert_eq!(elder.bull.len(), high.len());
        assert_eq!(elder.bear.len(), high.len());

        let fish = fisher(high.clone(), low.clone(), 3).expect("fisher");
        assert_eq!(fish.fisher.len(), high.len());
        assert_eq!(fish.signal.len(), high.len());

        let don = donchian(high.clone(), low.clone(), 3).expect("donchian");
        assert_eq!(don.upper.len(), high.len());
        assert_eq!(don.lower.len(), high.len());
        assert_eq!(don.middle.len(), high.len());

        let kel = keltner(high.clone(), low.clone(), close.clone(), 3, 3, 2.0).expect("keltner");
        assert_eq!(kel.upper.len(), high.len());
        assert_eq!(kel.middle.len(), high.len());
        assert_eq!(kel.lower.len(), high.len());

        let kling = klinger(high, low, close, volume, 3, 5, 2).expect("klinger");
        assert_eq!(kling.klinger.len(), values.len());
        assert_eq!(kling.signal.len(), values.len());
    }
}
