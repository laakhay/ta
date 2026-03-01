use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "obv",
    display_name: "On Balance Volume",
    category: "volume",
    aliases: &[],
    param_aliases: &[],
    params: &[],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "volume",
        description: "OBV value",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["close", "volume"],
        optional_fields: &[],
        lookback_params: &[],
        default_lookback: Some(2),
        warmup_policy: "none",
    },
    visual: VIS_VOLUME_LINE,
    runtime_binding: "obv",
};
