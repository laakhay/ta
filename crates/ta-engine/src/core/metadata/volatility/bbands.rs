use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
    id: "bbands",
    display_name: "Bollinger Bands",
    category: "volatility",
    aliases: &["bb", "bb_upper", "bb_lower"],
    param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
    params: &[P_PERIOD_20, P_STD_DEV_2],
    outputs: &[
        IndicatorOutputMeta {
            name: "upper",
            kind: "band_upper",
            description: "Upper band",
        },
        IndicatorOutputMeta {
            name: "middle",
            kind: "band_middle",
            description: "Middle band",
        },
        IndicatorOutputMeta {
            name: "lower",
            kind: "band_lower",
            description: "Lower band",
        },
    ],
    semantics: SEM_CLOSE_PERIOD,
    visual: VIS_BBANDS,
    runtime_binding: "bbands",
};
