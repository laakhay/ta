use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "fisher",
    display_name: "Fisher Transform",
    category: "trend",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[IndicatorParamMeta {
        name: "period",
        kind: IndicatorParamKind::Integer,
        required: false,
        default: Some("9"),
        description: "Lookback period",
        min: Some(1.0),
        max: None,
    }],
    outputs: &[
        IndicatorOutputMeta {
            name: "fisher",
            kind: "line",
            description: "Fisher value",
        },
        IndicatorOutputMeta {
            name: "signal",
            kind: "signal",
            description: "Signal value",
        },
    ],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low"],
        optional_fields: &[],
        lookback_params: &["period"],
        default_lookback: None,
        warmup_policy: "window",
    },
    visual: VIS_FISHER,
    runtime_binding: "fisher",
};
