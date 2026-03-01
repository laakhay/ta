use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "supertrend",
    display_name: "Supertrend",
    category: "trend",
    aliases: &[],
    param_aliases: &[],
    params: &[P_PERIOD_12, P_MULTIPLIER_3],
    outputs: &[
        IndicatorOutputMeta {
            name: "supertrend",
            kind: "line",
            description: "Supertrend line",
        },
        IndicatorOutputMeta {
            name: "direction",
            kind: "signal",
            description: "Trend direction",
        },
    ],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_SUPERTREND,
    runtime_binding: "supertrend",
};
