use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "crossdown",
    display_name: "Cross Down",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_A_SERIES, P_B_SERIES],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Cross down event",
    }],
    semantics: SEM_CLOSE_PAIR,
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "crossdown",
};
