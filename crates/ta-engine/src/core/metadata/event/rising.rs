use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "rising",
    display_name: "Rising",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_A_SERIES],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Rising event",
    }],
    semantics: SEM_CLOSE_NO_LOOKBACK,
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "rising",
};
