use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "ao",
    display_name: "Awesome Oscillator",
    category: "momentum",
    aliases: &[],
    param_aliases: &[],
    params: &[P_FAST_PERIOD_5, P_SLOW_PERIOD_34],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "column",
        description: "AO value",
    }],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low"],
        optional_fields: &[],
        lookback_params: &["fast_period", "slow_period"],
        default_lookback: None,
        warmup_policy: "window",
    },
    visual: VIS_VOLUME_HIST,
    runtime_binding: "ao",
};
