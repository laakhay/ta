use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "cmo",
    display_name: "Chande Momentum Oscillator",
    category: "momentum",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "CMO value",
    }],
    semantics: SEM_CLOSE_PERIOD,
    visual: VIS_OSC_LINE,
    runtime_binding: "cmo",
};
