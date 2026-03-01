use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "in_channel",
    display_name: "In Channel",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_PRICE_SERIES, P_UPPER_SERIES, P_LOWER_SERIES],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "In channel event",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["close"],
        optional_fields: &["upper", "lower"],
        lookback_params: &[],
        default_lookback: Some(1),
        warmup_policy: "none",
    },
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "in_channel",
};
