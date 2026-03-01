use super::*;

pub const ENTRIES: &[IndicatorMeta] = &[
    IndicatorMeta {
        id: "atr",
        display_name: "Average True Range",
        category: "volatility",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_14],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "ATR value",
        }],
        semantics: SEM_OHLC_PERIOD,
        visual: VIS_PRICE_LINE,
        runtime_binding: "atr",
    },
    IndicatorMeta {
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
    },
    IndicatorMeta {
        id: "donchian",
        display_name: "Donchian Channel",
        category: "volatility",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_20],
        outputs: &[
            IndicatorOutputMeta {
                name: "upper",
                kind: "band_upper",
                description: "Upper channel",
            },
            IndicatorOutputMeta {
                name: "lower",
                kind: "band_lower",
                description: "Lower channel",
            },
            IndicatorOutputMeta {
                name: "middle",
                kind: "band_middle",
                description: "Middle channel",
            },
        ],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["high", "low"],
            optional_fields: &[],
            lookback_params: &["period"],
            default_lookback: None,
            warmup_policy: "window",
        },
        visual: VIS_BBANDS,
        runtime_binding: "donchian",
    },
    IndicatorMeta {
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
    },
];
