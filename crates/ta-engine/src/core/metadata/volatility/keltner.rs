use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "keltner",
    display_name: "Keltner Channel",
    category: "volatility",
    aliases: &[],
    param_aliases: &[],
    params: &[P_EMA_PERIOD_20, P_ATR_PERIOD_10, P_MULTIPLIER_2],
    outputs: &[
        IndicatorOutputMeta {
            name: "upper",
            kind: "band_upper",
            description: "Upper channel",
        },
        IndicatorOutputMeta {
            name: "middle",
            kind: "band_middle",
            description: "Middle channel",
        },
        IndicatorOutputMeta {
            name: "lower",
            kind: "band_lower",
            description: "Lower channel",
        },
    ],
    semantics: SEM_OHLC_PERIOD,
    visual: VIS_BBANDS,
    runtime_binding: "keltner",
};
