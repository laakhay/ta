use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "ema",
    display_name: "Exponential Moving Average",
    category: "trend",
    aliases: &["rolling_ema"],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_20, P_SOURCE_STR],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "EMA value",
    }],
    semantics: SEM_CLOSE_PERIOD,
    visual: VIS_PRICE_LINE,
    runtime_binding: "ema",
};
