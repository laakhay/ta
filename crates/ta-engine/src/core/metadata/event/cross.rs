use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "cross",
    display_name: "Cross",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_A_SERIES, P_B_SERIES],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Any cross event",
    }],
    semantics: SEM_CLOSE_PAIR,
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "cross",
};
