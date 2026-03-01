use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "mfi",
    display_name: "Money Flow Index",
    category: "momentum",
    aliases: &[],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_14],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "MFI value",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low", "close", "volume"],
        optional_fields: &[],
        lookback_params: &["period"],
        default_lookback: None,
        warmup_policy: "window",
    },
    visual: VIS_OSC_LINE,
    runtime_binding: "mfi",
};
