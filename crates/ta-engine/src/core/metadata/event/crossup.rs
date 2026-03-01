use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "crossup",
    display_name: "Cross Up",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_A_SERIES, P_B_SERIES],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Cross up event",
    }],
    semantics: SEM_CLOSE_PAIR,
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "crossup",
};
