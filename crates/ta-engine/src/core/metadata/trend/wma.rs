use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "wma",
    display_name: "Weighted Moving Average",
    category: "trend",
    aliases: &["rolling_wma"],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14, P_SOURCE_STR],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "WMA value",
    }],
    semantics: SEM_CLOSE_PERIOD,
    visual: VIS_PRICE_LINE,
    runtime_binding: "wma",
};
