use serde_json::{Map, Value};

use crate::{core::events, metadata::find_indicator_meta};

use super::contracts::{
    ComputeIndicatorRequest, ComputeIndicatorResponse, ComputeRuntimeError, NamedSeries,
};
use super::params::normalize_params_for;

pub fn compute_indicator(
    req: ComputeIndicatorRequest,
) -> Result<ComputeIndicatorResponse, ComputeRuntimeError> {
    req.ohlcv.validate()?;
    let meta = find_indicator_meta(&req.indicator_id).ok_or_else(|| {
        ComputeRuntimeError::new(
            "unknown_indicator",
            format!("unknown indicator '{}'", req.indicator_id),
        )
    })?;
    let normalized_params = normalize_params_for(meta, &req.params)?;
    let params = normalized_params
        .as_object()
        .expect("normalize_params_for always returns object");

    let outputs = match meta.runtime_binding {
        "sma" => vec![line(
            meta.outputs[0].name,
            crate::rolling::rolling_mean(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
            ),
        )],
        "ema" => vec![line(
            meta.outputs[0].name,
            crate::moving_averages::ema(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
            ),
        )],
        "wma" => vec![line(
            meta.outputs[0].name,
            crate::moving_averages::wma(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
            ),
        )],
        "hma" => vec![line(
            meta.outputs[0].name,
            crate::moving_averages::hma(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
            ),
        )],
        "rsi" => vec![line(
            meta.outputs[0].name,
            crate::momentum::rsi(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
            ),
        )],
        "roc" => vec![line(
            meta.outputs[0].name,
            crate::momentum::roc(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
            ),
        )],
        "cmo" => vec![line(
            meta.outputs[0].name,
            crate::momentum::cmo(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
            ),
        )],
        "macd" => {
            let fast = p_usize(params, "fast_period")?;
            let slow = p_usize(params, "slow_period")?;
            let signal = p_usize(params, "signal_period")?;
            if fast >= slow {
                return Err(ComputeRuntimeError::new(
                    "invalid_param",
                    "fast_period must be less than slow_period",
                ));
            }
            let (macd, signal_line, histogram) = crate::trend::macd(
                series_param(&req, params, "source", "close")?,
                fast,
                slow,
                signal,
            );
            vec![
                line(meta.outputs[0].name, macd),
                line(meta.outputs[1].name, signal_line),
                line(meta.outputs[2].name, histogram),
            ]
        }
        "bbands" => {
            let (upper, middle, lower) = crate::volatility::bbands(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "period")?,
                p_f64(params, "std_dev")?,
            );
            vec![
                line(meta.outputs[0].name, upper),
                line(meta.outputs[1].name, middle),
                line(meta.outputs[2].name, lower),
            ]
        }
        "donchian" => {
            let (upper, lower, middle) = crate::volatility::donchian(
                &req.ohlcv.high,
                &req.ohlcv.low,
                p_usize(params, "period")?,
            );
            vec![
                line(meta.outputs[0].name, upper),
                line(meta.outputs[1].name, lower),
                line(meta.outputs[2].name, middle),
            ]
        }
        "keltner" => {
            let (upper, middle, lower) = crate::volatility::keltner(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "ema_period")?,
                p_usize(params, "atr_period")?,
                p_f64(params, "multiplier")?,
            );
            vec![
                line(meta.outputs[0].name, upper),
                line(meta.outputs[1].name, middle),
                line(meta.outputs[2].name, lower),
            ]
        }
        "atr" => vec![line(
            meta.outputs[0].name,
            crate::volatility::atr(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "period")?,
            ),
        )],
        "stochastic_kd" => {
            let (k, d) = crate::momentum::stochastic_kd(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "k_period")?,
                p_usize(params, "d_period")?,
                p_usize(params, "smooth")?,
            );
            vec![line(meta.outputs[0].name, k), line(meta.outputs[1].name, d)]
        }
        "obv" => vec![line(
            meta.outputs[0].name,
            crate::volume::obv(&req.ohlcv.close, volume(&req)?),
        )],
        "vwap" => vec![line(
            meta.outputs[0].name,
            crate::volume::vwap(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                volume(&req)?,
            ),
        )],
        "cmf" => vec![line(
            meta.outputs[0].name,
            crate::volume::cmf(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                volume(&req)?,
                p_usize(params, "period")?,
            ),
        )],
        "klinger_vf" => vec![line(
            meta.outputs[0].name,
            crate::volume::klinger_vf(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                volume(&req)?,
            ),
        )],
        "adx" => {
            let (adx, plus_di, minus_di) = crate::trend::adx(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "period")?,
            );
            vec![
                line(meta.outputs[0].name, adx),
                line(meta.outputs[1].name, plus_di),
                line(meta.outputs[2].name, minus_di),
            ]
        }
        "ao" => {
            let fast = p_usize(params, "fast_period")?;
            let slow = p_usize(params, "slow_period")?;
            if fast >= slow {
                return Err(ComputeRuntimeError::new(
                    "invalid_param",
                    "fast_period must be less than slow_period",
                ));
            }
            vec![line(
                meta.outputs[0].name,
                crate::momentum::ao(&req.ohlcv.high, &req.ohlcv.low, fast, slow),
            )]
        }
        "cci" => vec![line(
            meta.outputs[0].name,
            crate::momentum::cci(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "period")?,
            ),
        )],
        "williams_r" => vec![line(
            meta.outputs[0].name,
            crate::momentum::williams_r(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "period")?,
            ),
        )],
        "mfi" => vec![line(
            meta.outputs[0].name,
            crate::momentum::mfi(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                volume(&req)?,
                p_usize(params, "period")?,
            ),
        )],
        "vortex" => {
            let (plus, minus) = crate::momentum::vortex(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "period")?,
            );
            vec![
                line(meta.outputs[0].name, plus),
                line(meta.outputs[1].name, minus),
            ]
        }
        "coppock" => vec![line(
            meta.outputs[0].name,
            crate::momentum::coppock(
                series_param(&req, params, "source", "close")?,
                p_usize(params, "wma_period")?,
                p_usize(params, "fast_roc")?,
                p_usize(params, "slow_roc")?,
            ),
        )],
        "elder_ray" => {
            let (bull, bear) = crate::trend::elder_ray(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "period")?,
            );
            vec![
                line(meta.outputs[0].name, bull),
                line(meta.outputs[1].name, bear),
            ]
        }
        "ichimoku" => {
            let (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span) =
                crate::trend::ichimoku(
                    &req.ohlcv.high,
                    &req.ohlcv.low,
                    &req.ohlcv.close,
                    p_usize(params, "tenkan_period")?,
                    p_usize(params, "kijun_period")?,
                    p_usize(params, "span_b_period")?,
                    p_usize(params, "displacement")?,
                );
            vec![
                line(meta.outputs[0].name, tenkan_sen),
                line(meta.outputs[1].name, kijun_sen),
                line(meta.outputs[2].name, senkou_span_a),
                line(meta.outputs[3].name, senkou_span_b),
                line(meta.outputs[4].name, chikou_span),
            ]
        }
        "fisher" => {
            let (fisher, signal) =
                crate::trend::fisher(&req.ohlcv.high, &req.ohlcv.low, p_usize(params, "period")?);
            vec![
                line(meta.outputs[0].name, fisher),
                line(meta.outputs[1].name, signal),
            ]
        }
        "psar" => {
            let (sar, direction) = crate::trend::psar(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_f64(params, "af_start")?,
                p_f64(params, "af_increment")?,
                p_f64(params, "af_max")?,
            );
            vec![
                line(meta.outputs[0].name, sar),
                line(meta.outputs[1].name, direction),
            ]
        }
        "supertrend" => {
            let (supertrend, direction) = crate::trend::supertrend(
                &req.ohlcv.high,
                &req.ohlcv.low,
                &req.ohlcv.close,
                p_usize(params, "period")?,
                p_f64(params, "multiplier")?,
            );
            vec![
                line(meta.outputs[0].name, supertrend),
                line(meta.outputs[1].name, direction),
            ]
        }
        "swing_points_raw" => {
            let (highs, lows) = crate::trend::swing_points_raw(
                &req.ohlcv.high,
                &req.ohlcv.low,
                p_usize(params, "left")?,
                p_usize(params, "right")?,
                p_bool(params, "allow_equal_extremes")?,
            );
            vec![
                signal(meta.outputs[0].name, highs),
                signal(meta.outputs[1].name, lows),
            ]
        }
        "cross" => vec![signal(
            meta.outputs[0].name,
            events::cross(
                series_param(&req, params, "a", "close")?,
                series_param(&req, params, "b", "open")?,
            ),
        )],
        "crossup" => vec![signal(
            meta.outputs[0].name,
            events::crossup(
                series_param(&req, params, "a", "close")?,
                series_param(&req, params, "b", "open")?,
            ),
        )],
        "crossdown" => vec![signal(
            meta.outputs[0].name,
            events::crossdown(
                series_param(&req, params, "a", "close")?,
                series_param(&req, params, "b", "open")?,
            ),
        )],
        "rising" => vec![signal(
            meta.outputs[0].name,
            events::rising(series_param(&req, params, "a", "close")?),
        )],
        "falling" => vec![signal(
            meta.outputs[0].name,
            events::falling(series_param(&req, params, "a", "close")?),
        )],
        "rising_pct" => vec![signal(
            meta.outputs[0].name,
            events::rising_pct(
                series_param(&req, params, "a", "close")?,
                p_f64(params, "pct")?,
            ),
        )],
        "falling_pct" => vec![signal(
            meta.outputs[0].name,
            events::falling_pct(
                series_param(&req, params, "a", "close")?,
                p_f64(params, "pct")?,
            ),
        )],
        "in_channel" => vec![signal(
            meta.outputs[0].name,
            events::in_channel(
                series_param(&req, params, "price", "close")?,
                series_param(&req, params, "upper", "high")?,
                series_param(&req, params, "lower", "low")?,
            ),
        )],
        "out" => vec![signal(
            meta.outputs[0].name,
            events::out_channel(
                series_param(&req, params, "price", "close")?,
                series_param(&req, params, "upper", "high")?,
                series_param(&req, params, "lower", "low")?,
            ),
        )],
        "enter" => vec![signal(
            meta.outputs[0].name,
            events::enter_channel(
                series_param(&req, params, "price", "close")?,
                series_param(&req, params, "upper", "high")?,
                series_param(&req, params, "lower", "low")?,
            ),
        )],
        "exit" => vec![signal(
            meta.outputs[0].name,
            events::exit_channel(
                series_param(&req, params, "price", "close")?,
                series_param(&req, params, "upper", "high")?,
                series_param(&req, params, "lower", "low")?,
            ),
        )],
        _ => {
            return Err(ComputeRuntimeError::new(
                "unsupported_indicator",
                format!(
                    "runtime binding '{}' is not supported",
                    meta.runtime_binding
                ),
            ));
        }
    };

    Ok(ComputeIndicatorResponse {
        indicator_id: meta.id.to_string(),
        runtime_binding: meta.runtime_binding.to_string(),
        instance_id: req.instance_id,
        outputs,
        visual: meta.visual,
        normalized_params,
    })
}

fn p_usize(params: &Map<String, Value>, name: &str) -> Result<usize, ComputeRuntimeError> {
    params
        .get(name)
        .and_then(|v| {
            v.as_u64()
                .or_else(|| v.as_i64().and_then(|x| (x >= 0).then_some(x as u64)))
        })
        .map(|v| v as usize)
        .ok_or_else(|| {
            ComputeRuntimeError::new("invalid_param", format!("missing/invalid '{name}'"))
        })
}

fn p_f64(params: &Map<String, Value>, name: &str) -> Result<f64, ComputeRuntimeError> {
    params.get(name).and_then(Value::as_f64).ok_or_else(|| {
        ComputeRuntimeError::new("invalid_param", format!("missing/invalid '{name}'"))
    })
}

fn p_bool(params: &Map<String, Value>, name: &str) -> Result<bool, ComputeRuntimeError> {
    params.get(name).and_then(Value::as_bool).ok_or_else(|| {
        ComputeRuntimeError::new("invalid_param", format!("missing/invalid '{name}'"))
    })
}

fn line(name: &str, values: Vec<f64>) -> NamedSeries {
    NamedSeries {
        name: name.to_string(),
        values: values
            .into_iter()
            .map(|v| if v.is_nan() { None } else { Some(v) })
            .collect(),
    }
}

fn signal(name: &str, values: Vec<bool>) -> NamedSeries {
    NamedSeries {
        name: name.to_string(),
        values: values
            .into_iter()
            .map(|v| if v { Some(1.0) } else { Some(0.0) })
            .collect(),
    }
}

fn series_param<'a>(
    req: &'a ComputeIndicatorRequest,
    params: &'a Map<String, Value>,
    name: &str,
    fallback: &'a str,
) -> Result<&'a [f64], ComputeRuntimeError> {
    let field = params
        .get(name)
        .and_then(Value::as_str)
        .filter(|v| !v.trim().is_empty())
        .unwrap_or(fallback);
    ohlcv_field(req, field)
}

fn ohlcv_field<'a>(
    req: &'a ComputeIndicatorRequest,
    field: &str,
) -> Result<&'a [f64], ComputeRuntimeError> {
    match field.to_ascii_lowercase().as_str() {
        "open" => Ok(&req.ohlcv.open),
        "high" => Ok(&req.ohlcv.high),
        "low" => Ok(&req.ohlcv.low),
        "close" => Ok(&req.ohlcv.close),
        "volume" => volume(req),
        _ => Err(ComputeRuntimeError::new(
            "missing_input_field",
            format!("unknown input field '{field}'"),
        )),
    }
}

fn volume(req: &ComputeIndicatorRequest) -> Result<&[f64], ComputeRuntimeError> {
    req.ohlcv
        .volume
        .as_deref()
        .ok_or_else(|| ComputeRuntimeError::new("missing_input_field", "volume input is required"))
}
