use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "coppock",
    display_name: "Coppock Curve",
    category: "momentum",
    aliases: &[],
    param_aliases: &[],
    params: &[
        IndicatorParamMeta {
            name: "wma_period",
            kind: IndicatorParamKind::Integer,
            required: false,
            default: Some("10"),
            description: "WMA period",
            min: Some(1.0),
            max: None,
        },
        IndicatorParamMeta {
            name: "fast_roc",
            kind: IndicatorParamKind::Integer,
            required: false,
            default: Some("11"),
            description: "Fast ROC period",
            min: Some(1.0),
            max: None,
        },
        IndicatorParamMeta {
            name: "slow_roc",
            kind: IndicatorParamKind::Integer,
            required: false,
            default: Some("14"),
            description: "Slow ROC period",
            min: Some(1.0),
            max: None,
        },
    ],
    outputs: &[IndicatorOutputMeta {
        name: "result",
        kind: "line",
        description: "Coppock value",
    }],
    semantics: SEM_CLOSE_FAST_SLOW_SIGNAL,
    visual: VIS_OSC_LINE,
    runtime_binding: "coppock",
};
