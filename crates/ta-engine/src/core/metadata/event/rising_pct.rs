use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "rising_pct",
    display_name: "Rising By Percent",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_A_SERIES, P_PCT_5],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Rising by percent event",
    }],
    semantics: SEM_CLOSE_NO_LOOKBACK,
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "rising_pct",
};
