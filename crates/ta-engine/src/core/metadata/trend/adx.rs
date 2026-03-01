use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "adx",
    display_name: "Average Directional Index",
    category: "trend",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14],
    outputs: &[
        IndicatorOutputMeta {
            name: "adx",
            kind: "line",
            description: "ADX value",
        },
        IndicatorOutputMeta {
            name: "plus_di",
            kind: "line",
            description: "Positive directional indicator",
        },
        IndicatorOutputMeta {
            name: "minus_di",
            kind: "line",
            description: "Negative directional indicator",
        },
    ],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_ADX,
    runtime_binding: "adx",
};
