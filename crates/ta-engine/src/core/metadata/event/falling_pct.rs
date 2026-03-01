use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "falling_pct",
    display_name: "Falling By Percent",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_A_SERIES, P_PCT_5],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Falling by percent event",
    }],
    semantics: SEM_CLOSE_NO_LOOKBACK,
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "falling_pct",
};
