use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "klinger_vf",
    display_name: "Klinger Volume Force",
    category: "volume",
    aliases: &["klinger"],
    param_aliases: &[],
    params: &[],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "volume",
        description: "Raw Klinger volume force",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low", "close", "volume"],
        optional_fields: &[],
        lookback_params: &[],
        default_lookback: Some(1),
        warmup_policy: "none",
    },
    visual: VIS_VOLUME_LINE,
    runtime_binding: "klinger_vf",
};
