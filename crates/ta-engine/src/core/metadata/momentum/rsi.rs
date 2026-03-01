use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "rsi",
    display_name: "Relative Strength Index",
    category: "momentum",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "RSI value",
    }],
    semantics: SEM_CLOSE_PERIOD,
    visual: VIS_OSC_LINE,
    runtime_binding: "rsi",
};
