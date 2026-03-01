use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "williams_r",
    display_name: "Williams %R",
    category: "momentum",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "Williams %R value",
    }],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_OSC_LINE,
    runtime_binding: "williams_r",
};
