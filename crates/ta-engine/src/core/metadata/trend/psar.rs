use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "psar",
    display_name: "Parabolic SAR",
    category: "trend",
    aliases: &[],
    param_aliases: &[],
    params: &[P_AF_START_002, P_AF_INCREMENT_002, P_AF_MAX_02],
    outputs: &[
        IndicatorOutputMeta {
            name: "sar",
            kind: "line",
            description: "SAR value",
        },
        IndicatorOutputMeta {
            name: "direction",
            kind: "signal",
            description: "Trend direction",
        },
    ],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_PSAR,
    runtime_binding: "psar",
};
