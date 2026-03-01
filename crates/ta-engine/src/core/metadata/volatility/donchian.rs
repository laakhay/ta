use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "donchian",
    display_name: "Donchian Channel",
    category: "volatility",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_20],
    outputs: &[
        IndicatorOutputMeta {
            name: "upper",
            kind: "band_upper",
            description: "Upper channel",
        },
        IndicatorOutputMeta {
            name: "lower",
            kind: "band_lower",
            description: "Lower channel",
        },
        IndicatorOutputMeta {
            name: "middle",
            kind: "band_middle",
            description: "Middle channel",
        },
    ],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low"],
        optional_fields: &[],
        lookback_params: &["period"],
        default_lookback: None,
        warmup_policy: "window",
    },
    visual: VIS_BBANDS,
    runtime_binding: "donchian",
};
