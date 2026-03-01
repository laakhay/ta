use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "vwap",
    display_name: "Volume Weighted Average Price",
    category: "volume",
    aliases: &[],
    param_aliases: &[],
    params: &[],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "volume",
        description: "VWAP value",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low", "close", "volume"],
        optional_fields: &[],
        lookback_params: &[],
        default_lookback: Some(1),
        warmup_policy: "none",
    },
    visual: VIS_PRICE_LINE,
    runtime_binding: "vwap",
};
