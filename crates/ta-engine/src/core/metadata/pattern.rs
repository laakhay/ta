use super::*;

pub const ENTRIES: &[IndicatorMeta] = &[IndicatorMeta {
    id: "swing_points",
    display_name: "Swing Points",
    category: "pattern",
    aliases: &[
        "swing_points_raw",
        "swing_highs",
        "swing_lows",
        "swing_high_at",
        "swing_low_at",
    ],
    param_aliases: &[],
    params: &[P_LEFT_2, P_RIGHT_2, P_ALLOW_EQUAL_FALSE],
    outputs: &[
        IndicatorOutputMeta {
            name: "swing_high",
            kind: "signal",
            description: "Swing high event flag",
        },
        IndicatorOutputMeta {
            name: "swing_low",
            kind: "signal",
            description: "Swing low event flag",
        },
    ],
    semantics: IndicatorSemanticsMeta {
        required_fields: &["high", "low"],
        optional_fields: &[],
        lookback_params: &["left", "right"],
        default_lookback: None,
        warmup_policy: "window",
    },
    visual: VIS_SWING_POINTS,
    runtime_binding: "swing_points_raw",
}];
