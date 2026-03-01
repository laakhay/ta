use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "ichimoku",
    display_name: "Ichimoku Cloud",
    category: "trend",
    aliases: &[],
    param_aliases: &[],
    params: &[P_TENKAN_9, P_KIJUN_26, P_SPAN_B_52, P_DISPLACEMENT_26],
    outputs: &[
        IndicatorOutputMeta {
            name: "tenkan_sen",
            kind: "line",
            description: "Tenkan-sen",
        },
        IndicatorOutputMeta {
            name: "kijun_sen",
            kind: "line",
            description: "Kijun-sen",
        },
        IndicatorOutputMeta {
            name: "senkou_span_a",
            kind: "line",
            description: "Senkou Span A",
        },
        IndicatorOutputMeta {
            name: "senkou_span_b",
            kind: "line",
            description: "Senkou Span B",
        },
        IndicatorOutputMeta {
            name: "chikou_span",
            kind: "line",
            description: "Chikou Span",
        },
    ],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_ICHIMOKU,
    runtime_binding: "ichimoku",
};
