use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "elder_ray",
    display_name: "Elder Ray Index",
    category: "trend",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[IndicatorParamMeta {
        name: "period",
        kind: IndicatorParamKind::Integer,
        required: false,
        default: Some("13"),
        description: "EMA period",
        min: Some(1.0),
        max: None,
    }],
    outputs: &[
        IndicatorOutputMeta {
            name: "bull",
            kind: "histogram",
            description: "Bull power",
        },
        IndicatorOutputMeta {
            name: "bear",
            kind: "histogram",
            description: "Bear power",
        },
    ],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_ELDER_RAY,
    runtime_binding: "elder_ray",
};
