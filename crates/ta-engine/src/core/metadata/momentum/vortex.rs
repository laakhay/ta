use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "vortex",
    display_name: "Vortex Indicator",
    category: "momentum",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14],
    outputs: &[
        IndicatorOutputMeta {
            name: "plus",
            kind: "line",
            description: "VI+",
        },
        IndicatorOutputMeta {
            name: "minus",
            kind: "line",
            description: "VI-",
        },
    ],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_VORTEX,
    runtime_binding: "vortex",
};
