use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "cmf",
    display_name: "Chaikin Money Flow",
    category: "volume",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_20],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "volume",
        description: "CMF value",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low", "close", "volume"],
        optional_fields: &[],
        lookback_params: &["period"],
        default_lookback: None,
        warmup_policy: "window",
    },
    visual: VIS_VOLUME_LINE,
    runtime_binding: "cmf",
};
