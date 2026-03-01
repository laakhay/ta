use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "falling",
    display_name: "Falling",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_A_SERIES],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Falling event",
    }],
    semantics: SEM_CLOSE_NO_LOOKBACK,
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "falling",
};
