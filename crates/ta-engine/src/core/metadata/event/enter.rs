use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "enter",
    display_name: "Enter Channel",
    category: "event",
    aliases: &[],
    param_aliases: &[],
    params: &[P_PRICE_SERIES, P_UPPER_SERIES, P_LOWER_SERIES],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "signal",
        description: "Enter channel event",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["close"],
        optional_fields: &["upper", "lower"],
        lookback_params: &[],
        default_lookback: Some(2),
        warmup_policy: "none",
    },
    visual: VIS_SIGNAL_FLAG,
    runtime_binding: "enter",
};
