use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "hma",
    display_name: "Hull Moving Average",
    category: "trend",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "HMA value",
    }],
    semantics: SEM_CLOSE_PERIOD,
    visual: VIS_PRICE_LINE,
    runtime_binding: "hma",
};
