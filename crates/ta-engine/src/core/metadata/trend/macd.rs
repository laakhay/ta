use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "macd",
    display_name: "Moving Average Convergence Divergence",
    category: "trend",
    aliases: &[],
    param_aliases: &[],
    params: &[P_FAST_PERIOD_12, P_SLOW_PERIOD_26, P_SIGNAL_PERIOD_9],
    outputs: &[
        IndicatorOutputMeta {
            name: "macd",
            kind: "line",
            description: "MACD line",
        },
        IndicatorOutputMeta {
            name: "signal",
            kind: "signal",
            description: "Signal line",
        },
        IndicatorOutputMeta {
            name: "histogram",
            kind: "histogram",
            description: "MACD histogram",
        },
    ],
    semantics: SEM_CLOSE_FAST_SLOW_SIGNAL,
    visual: VIS_MACD,
    runtime_binding: "macd",
};
