use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "sma",
    display_name: "Simple Moving Average",
    category: "trend",
    aliases: &["rolling_mean", "mean"],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_20, P_SOURCE_STR],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "SMA value",
    }],
    semantics: SEM_CLOSE_PERIOD,
    visual: VIS_PRICE_LINE,
    runtime_binding: "sma",
};
