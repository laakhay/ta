//! Canonical indicator metadata catalog for Rust-first compute/runtime ownership.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IndicatorParamKind {
    Integer,
    Float,
    Boolean,
    String,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct IndicatorParamMeta {
    pub name: &'static str,
    pub kind: IndicatorParamKind,
    pub required: bool,
    pub default: Option<&'static str>,
    pub description: &'static str,
    pub min: Option<f64>,
    pub max: Option<f64>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct IndicatorOutputMeta {
    pub name: &'static str,
    pub kind: &'static str,
    pub description: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct IndicatorSemanticsMeta {
    pub required_fields: &'static [&'static str],
    pub optional_fields: &'static [&'static str],
    pub lookback_params: &'static [&'static str],
    pub default_lookback: Option<usize>,
    pub warmup_policy: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct IndicatorAliasMeta {
    pub alias: &'static str,
    pub target: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct IndicatorMeta {
    pub id: &'static str,
    pub display_name: &'static str,
    pub category: &'static str,
    pub aliases: &'static [&'static str],
    pub param_aliases: &'static [IndicatorAliasMeta],
    pub params: &'static [IndicatorParamMeta],
    pub outputs: &'static [IndicatorOutputMeta],
    pub semantics: IndicatorSemanticsMeta,
    pub runtime_binding: &'static str,
}

const P_PERIOD_14: IndicatorParamMeta = IndicatorParamMeta {
    name: "period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("14"),
    description: "Lookback period",
    min: Some(1.0),
    max: None,
};

const P_PERIOD_12: IndicatorParamMeta = IndicatorParamMeta {
    name: "period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("12"),
    description: "Lookback period",
    min: Some(1.0),
    max: None,
};

const P_PERIOD_20: IndicatorParamMeta = IndicatorParamMeta {
    name: "period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("20"),
    description: "Lookback period",
    min: Some(1.0),
    max: None,
};

const P_FAST_PERIOD_12: IndicatorParamMeta = IndicatorParamMeta {
    name: "fast_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("12"),
    description: "Fast moving average period",
    min: Some(1.0),
    max: None,
};

const P_FAST_PERIOD_5: IndicatorParamMeta = IndicatorParamMeta {
    name: "fast_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("5"),
    description: "Fast moving average period",
    min: Some(1.0),
    max: None,
};

const P_SLOW_PERIOD_26: IndicatorParamMeta = IndicatorParamMeta {
    name: "slow_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("26"),
    description: "Slow moving average period",
    min: Some(1.0),
    max: None,
};

const P_SLOW_PERIOD_34: IndicatorParamMeta = IndicatorParamMeta {
    name: "slow_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("34"),
    description: "Slow moving average period",
    min: Some(1.0),
    max: None,
};

const P_SIGNAL_PERIOD_9: IndicatorParamMeta = IndicatorParamMeta {
    name: "signal_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("9"),
    description: "Signal period",
    min: Some(1.0),
    max: None,
};

const P_STD_DEV_2: IndicatorParamMeta = IndicatorParamMeta {
    name: "std_dev",
    kind: IndicatorParamKind::Float,
    required: false,
    default: Some("2.0"),
    description: "Standard deviation multiplier",
    min: Some(0.0),
    max: None,
};

const P_PCT_5: IndicatorParamMeta = IndicatorParamMeta {
    name: "pct",
    kind: IndicatorParamKind::Float,
    required: false,
    default: Some("5"),
    description: "Percentage threshold",
    min: Some(0.0),
    max: None,
};

const P_K_PERIOD_14: IndicatorParamMeta = IndicatorParamMeta {
    name: "k_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("14"),
    description: "Fast stochastic lookback",
    min: Some(1.0),
    max: None,
};

const P_D_PERIOD_3: IndicatorParamMeta = IndicatorParamMeta {
    name: "d_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("3"),
    description: "Signal smoothing period",
    min: Some(1.0),
    max: None,
};

const P_SMOOTH_1: IndicatorParamMeta = IndicatorParamMeta {
    name: "smooth",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("1"),
    description: "Pre-smoothing for stochastic K",
    min: Some(1.0),
    max: None,
};

const P_LEFT_2: IndicatorParamMeta = IndicatorParamMeta {
    name: "left",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("2"),
    description: "Left pivot lookback",
    min: Some(1.0),
    max: None,
};

const P_RIGHT_2: IndicatorParamMeta = IndicatorParamMeta {
    name: "right",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("2"),
    description: "Right pivot lookback",
    min: Some(1.0),
    max: None,
};

const P_ALLOW_EQUAL_FALSE: IndicatorParamMeta = IndicatorParamMeta {
    name: "allow_equal_extremes",
    kind: IndicatorParamKind::Boolean,
    required: false,
    default: Some("false"),
    description: "Allow equality while detecting extrema",
    min: None,
    max: None,
};

const PARAM_ALIAS_LOOKBACK_PERIOD: IndicatorAliasMeta = IndicatorAliasMeta {
    alias: "lookback",
    target: "period",
};

const SEM_CLOSE_PERIOD: IndicatorSemanticsMeta = IndicatorSemanticsMeta {
    required_fields: &["close"],
    optional_fields: &[],
    lookback_params: &["period"],
    default_lookback: None,
    warmup_policy: "window",
};

const SEM_CLOSE_FAST_SLOW_SIGNAL: IndicatorSemanticsMeta = IndicatorSemanticsMeta {
    required_fields: &["close"],
    optional_fields: &[],
    lookback_params: &["fast_period", "slow_period", "signal_period"],
    default_lookback: None,
    warmup_policy: "window",
};

const SEM_OHLC_PERIOD: IndicatorSemanticsMeta = IndicatorSemanticsMeta {
    required_fields: &["high", "low", "close"],
    optional_fields: &[],
    lookback_params: &["period"],
    default_lookback: None,
    warmup_policy: "window",
};

const SEM_OHLC_STOCH: IndicatorSemanticsMeta = IndicatorSemanticsMeta {
    required_fields: &["high", "low", "close"],
    optional_fields: &[],
    lookback_params: &["k_period", "d_period", "smooth"],
    default_lookback: None,
    warmup_policy: "window",
};

const SEM_CLOSE_NO_LOOKBACK: IndicatorSemanticsMeta = IndicatorSemanticsMeta {
    required_fields: &["close"],
    optional_fields: &[],
    lookback_params: &[],
    default_lookback: Some(1),
    warmup_policy: "none",
};

const SEM_CLOSE_PAIR: IndicatorSemanticsMeta = IndicatorSemanticsMeta {
    required_fields: &["close"],
    optional_fields: &["close_b"],
    lookback_params: &[],
    default_lookback: Some(2),
    warmup_policy: "none",
};

const CATALOG: &[IndicatorMeta] = &[
    IndicatorMeta {
        id: "adx",
        display_name: "Average Directional Index",
        category: "trend",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_14],
        outputs: &[
            IndicatorOutputMeta {
                name: "adx",
                kind: "line",
                description: "ADX value",
            },
            IndicatorOutputMeta {
                name: "plus_di",
                kind: "line",
                description: "Positive directional indicator",
            },
            IndicatorOutputMeta {
                name: "minus_di",
                kind: "line",
                description: "Negative directional indicator",
            },
        ],
        semantics: SEM_OHLC_PERIOD,
        runtime_binding: "adx",
    },
    IndicatorMeta {
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
        runtime_binding: "ao",
    },
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
        runtime_binding: "bbands",
    },
    IndicatorMeta {
        id: "cci",
        display_name: "Commodity Channel Index",
        category: "momentum",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_20],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "CCI value",
        }],
        semantics: SEM_OHLC_PERIOD,
        runtime_binding: "cci",
    },
    IndicatorMeta {
        id: "cmf",
        display_name: "Chaikin Money Flow",
        category: "volume",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_20],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "volume",
            description: "CMF value",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["high", "low", "close", "volume"],
            optional_fields: &[],
            lookback_params: &["period"],
            default_lookback: None,
            warmup_policy: "window",
        },
        runtime_binding: "cmf",
    },
    IndicatorMeta {
        id: "cmo",
        display_name: "Chande Momentum Oscillator",
        category: "momentum",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_14],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "CMO value",
        }],
        semantics: SEM_CLOSE_PERIOD,
        runtime_binding: "cmo",
    },
    IndicatorMeta {
        id: "cross",
        display_name: "Cross",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Any cross event",
        }],
        semantics: SEM_CLOSE_PAIR,
        runtime_binding: "cross",
    },
    IndicatorMeta {
        id: "crossdown",
        display_name: "Cross Down",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Cross down event",
        }],
        semantics: SEM_CLOSE_PAIR,
        runtime_binding: "crossdown",
    },
    IndicatorMeta {
        id: "crossup",
        display_name: "Cross Up",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Cross up event",
        }],
        semantics: SEM_CLOSE_PAIR,
        runtime_binding: "crossup",
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
        semantics: IndicatorSemanticsMeta {
            required_fields: &["high", "low"],
            optional_fields: &[],
            lookback_params: &["period"],
            default_lookback: None,
            warmup_policy: "window",
        },
        runtime_binding: "donchian",
    },
    IndicatorMeta {
        id: "ema",
        display_name: "Exponential Moving Average",
        category: "trend",
        aliases: &["rolling_ema"],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_20],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "EMA value",
        }],
        semantics: SEM_CLOSE_PERIOD,
        runtime_binding: "ema",
    },
    IndicatorMeta {
        id: "enter",
        display_name: "Enter Channel",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Enter channel event",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["close"],
            optional_fields: &["upper", "lower"],
            lookback_params: &[],
            default_lookback: Some(2),
            warmup_policy: "none",
        },
        runtime_binding: "enter",
    },
    IndicatorMeta {
        id: "exit",
        display_name: "Exit Channel",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Exit channel event",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["close"],
            optional_fields: &["upper", "lower"],
            lookback_params: &[],
            default_lookback: Some(2),
            warmup_policy: "none",
        },
        runtime_binding: "exit",
    },
    IndicatorMeta {
        id: "falling",
        display_name: "Falling",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Falling event",
        }],
        semantics: SEM_CLOSE_NO_LOOKBACK,
        runtime_binding: "falling",
    },
    IndicatorMeta {
        id: "falling_pct",
        display_name: "Falling By Percent",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[P_PCT_5],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Falling by percent event",
        }],
        semantics: SEM_CLOSE_NO_LOOKBACK,
        runtime_binding: "falling_pct",
    },
    IndicatorMeta {
        id: "in_channel",
        display_name: "In Channel",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "In channel event",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["close"],
            optional_fields: &["upper", "lower"],
            lookback_params: &[],
            default_lookback: Some(1),
            warmup_policy: "none",
        },
        runtime_binding: "in_channel",
    },
    IndicatorMeta {
        id: "keltner",
        display_name: "Keltner Channel",
        category: "volatility",
        aliases: &[],
        param_aliases: &[],
        params: &[P_PERIOD_20, P_PERIOD_14, P_STD_DEV_2],
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
        runtime_binding: "keltner",
    },
    IndicatorMeta {
        id: "klinger_vf",
        display_name: "Klinger Volume Force",
        category: "volume",
        aliases: &["klinger"],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "volume",
            description: "Raw Klinger volume force",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["high", "low", "close", "volume"],
            optional_fields: &[],
            lookback_params: &[],
            default_lookback: Some(1),
            warmup_policy: "none",
        },
        runtime_binding: "klinger_vf",
    },
    IndicatorMeta {
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
        runtime_binding: "macd",
    },
    IndicatorMeta {
        id: "obv",
        display_name: "On Balance Volume",
        category: "volume",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "volume",
            description: "OBV value",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["close", "volume"],
            optional_fields: &[],
            lookback_params: &[],
            default_lookback: Some(2),
            warmup_policy: "none",
        },
        runtime_binding: "obv",
    },
    IndicatorMeta {
        id: "out",
        display_name: "Out Of Channel",
        category: "event",
        aliases: &["out_channel"],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Out of channel event",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["close"],
            optional_fields: &["upper", "lower"],
            lookback_params: &[],
            default_lookback: Some(1),
            warmup_policy: "none",
        },
        runtime_binding: "out",
    },
    IndicatorMeta {
        id: "rising",
        display_name: "Rising",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Rising event",
        }],
        semantics: SEM_CLOSE_NO_LOOKBACK,
        runtime_binding: "rising",
    },
    IndicatorMeta {
        id: "rising_pct",
        display_name: "Rising By Percent",
        category: "event",
        aliases: &[],
        param_aliases: &[],
        params: &[P_PCT_5],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "signal",
            description: "Rising by percent event",
        }],
        semantics: SEM_CLOSE_NO_LOOKBACK,
        runtime_binding: "rising_pct",
    },
    IndicatorMeta {
        id: "roc",
        display_name: "Rate of Change",
        category: "momentum",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_12],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "ROC value",
        }],
        semantics: SEM_CLOSE_PERIOD,
        runtime_binding: "roc",
    },
    IndicatorMeta {
        id: "rsi",
        display_name: "Relative Strength Index",
        category: "momentum",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_14],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "RSI value",
        }],
        semantics: SEM_CLOSE_PERIOD,
        runtime_binding: "rsi",
    },
    IndicatorMeta {
        id: "sma",
        display_name: "Simple Moving Average",
        category: "trend",
        aliases: &["rolling_mean", "mean"],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_20],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "SMA value",
        }],
        semantics: SEM_CLOSE_PERIOD,
        runtime_binding: "sma",
    },
    IndicatorMeta {
        id: "stochastic",
        display_name: "Stochastic Oscillator",
        category: "momentum",
        aliases: &["stoch", "stochastic_kd", "stoch_k", "stoch_d"],
        param_aliases: &[],
        params: &[P_K_PERIOD_14, P_D_PERIOD_3, P_SMOOTH_1],
        outputs: &[
            IndicatorOutputMeta {
                name: "k",
                kind: "osc_main",
                description: "K line",
            },
            IndicatorOutputMeta {
                name: "d",
                kind: "osc_signal",
                description: "D line",
            },
        ],
        semantics: SEM_OHLC_STOCH,
        runtime_binding: "stochastic_kd",
    },
    IndicatorMeta {
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
        runtime_binding: "swing_points_raw",
    },
    IndicatorMeta {
        id: "vwap",
        display_name: "Volume Weighted Average Price",
        category: "volume",
        aliases: &[],
        param_aliases: &[],
        params: &[],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "volume",
            description: "VWAP value",
        }],
        semantics: IndicatorSemanticsMeta {
            required_fields: &["high", "low", "close", "volume"],
            optional_fields: &[],
            lookback_params: &[],
            default_lookback: Some(1),
            warmup_policy: "none",
        },
        runtime_binding: "vwap",
    },
    IndicatorMeta {
        id: "williams_r",
        display_name: "Williams %R",
        category: "momentum",
        aliases: &[],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_14],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "Williams %R value",
        }],
        semantics: SEM_OHLC_PERIOD,
        runtime_binding: "williams_r",
    },
    IndicatorMeta {
        id: "wma",
        display_name: "Weighted Moving Average",
        category: "trend",
        aliases: &["rolling_wma"],
        param_aliases: &[PARAM_ALIAS_LOOKBACK_PERIOD],
        params: &[P_PERIOD_14],
        outputs: &[IndicatorOutputMeta {
            name: "result",
            kind: "line",
            description: "WMA value",
        }],
        semantics: SEM_CLOSE_PERIOD,
        runtime_binding: "wma",
    },
];

/// Returns the canonical indicator catalog exposed by Rust compute.
pub fn indicator_catalog() -> &'static [IndicatorMeta] {
    CATALOG
}

/// Finds indicator metadata by id or alias.
pub fn find_indicator_meta(id: &str) -> Option<&'static IndicatorMeta> {
    indicator_catalog().iter().find(|meta| {
        meta.id.eq_ignore_ascii_case(id)
            || meta
                .aliases
                .iter()
                .any(|alias| alias.eq_ignore_ascii_case(id))
    })
}
