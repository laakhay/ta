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
pub enum IndicatorPaneHint {
    PriceOverlay,
    SeparatePane,
    VolumeOverlay,
    Auto,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IndicatorScaleGroup {
    Price,
    Oscillator,
    Volume,
    Normalized,
    Binary,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OutputVisualPrimitive {
    Line,
    Histogram,
    BandFill,
    Markers,
    SignalFlag,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StrokePattern {
    Solid,
    Dashed,
    Dotted,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StyleSlotType {
    Stroke,
    Fill,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct StyleDefaultMeta {
    pub color: &'static str,
    pub width: Option<f64>,
    pub opacity: Option<f64>,
    pub pattern: Option<StrokePattern>,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct StyleSlotMeta {
    pub slot: &'static str,
    pub kind: StyleSlotType,
    pub default: StyleDefaultMeta,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OutputVisualMeta {
    pub output: &'static str,
    pub primitive: OutputVisualPrimitive,
    pub style_slot: &'static str,
    pub z_index: i32,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct IndicatorVisualMeta {
    pub pane_hint: IndicatorPaneHint,
    pub scale_group: IndicatorScaleGroup,
    pub output_visuals: &'static [OutputVisualMeta],
    pub style_slots: &'static [StyleSlotMeta],
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
    pub visual: IndicatorVisualMeta,
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
const P_SOURCE_STR: IndicatorParamMeta = IndicatorParamMeta {
    name: "source",
    kind: IndicatorParamKind::String,
    required: false,
    default: None,
    description: "Source field override",
    min: None,
    max: None,
};
const P_A_SERIES: IndicatorParamMeta = IndicatorParamMeta {
    name: "a",
    kind: IndicatorParamKind::String,
    required: false,
    default: None,
    description: "Primary series input",
    min: None,
    max: None,
};
const P_B_SERIES: IndicatorParamMeta = IndicatorParamMeta {
    name: "b",
    kind: IndicatorParamKind::String,
    required: false,
    default: None,
    description: "Secondary series input",
    min: None,
    max: None,
};
const P_PRICE_SERIES: IndicatorParamMeta = IndicatorParamMeta {
    name: "price",
    kind: IndicatorParamKind::String,
    required: false,
    default: None,
    description: "Price series input",
    min: None,
    max: None,
};
const P_UPPER_SERIES: IndicatorParamMeta = IndicatorParamMeta {
    name: "upper",
    kind: IndicatorParamKind::String,
    required: false,
    default: None,
    description: "Upper bound input",
    min: None,
    max: None,
};
const P_LOWER_SERIES: IndicatorParamMeta = IndicatorParamMeta {
    name: "lower",
    kind: IndicatorParamKind::String,
    required: false,
    default: None,
    description: "Lower bound input",
    min: None,
    max: None,
};

const P_MULTIPLIER_3: IndicatorParamMeta = IndicatorParamMeta {
    name: "multiplier",
    kind: IndicatorParamKind::Float,
    required: false,
    default: Some("3.0"),
    description: "Channel multiplier",
    min: Some(0.0),
    max: None,
};
const P_MULTIPLIER_2: IndicatorParamMeta = IndicatorParamMeta {
    name: "multiplier",
    kind: IndicatorParamKind::Float,
    required: false,
    default: Some("2.0"),
    description: "Channel multiplier",
    min: Some(0.0),
    max: None,
};
const P_EMA_PERIOD_20: IndicatorParamMeta = IndicatorParamMeta {
    name: "ema_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("20"),
    description: "EMA period",
    min: Some(1.0),
    max: None,
};
const P_ATR_PERIOD_10: IndicatorParamMeta = IndicatorParamMeta {
    name: "atr_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("10"),
    description: "ATR period",
    min: Some(1.0),
    max: None,
};

const P_TENKAN_9: IndicatorParamMeta = IndicatorParamMeta {
    name: "tenkan_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("9"),
    description: "Tenkan-sen period",
    min: Some(1.0),
    max: None,
};

const P_KIJUN_26: IndicatorParamMeta = IndicatorParamMeta {
    name: "kijun_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("26"),
    description: "Kijun-sen period",
    min: Some(1.0),
    max: None,
};

const P_SPAN_B_52: IndicatorParamMeta = IndicatorParamMeta {
    name: "span_b_period",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("52"),
    description: "Senkou Span B period",
    min: Some(1.0),
    max: None,
};

const P_DISPLACEMENT_26: IndicatorParamMeta = IndicatorParamMeta {
    name: "displacement",
    kind: IndicatorParamKind::Integer,
    required: false,
    default: Some("26"),
    description: "Ichimoku displacement",
    min: Some(1.0),
    max: None,
};

const P_AF_START_002: IndicatorParamMeta = IndicatorParamMeta {
    name: "af_start",
    kind: IndicatorParamKind::Float,
    required: false,
    default: Some("0.02"),
    description: "Initial acceleration factor",
    min: Some(0.0),
    max: None,
};

const P_AF_INCREMENT_002: IndicatorParamMeta = IndicatorParamMeta {
    name: "af_increment",
    kind: IndicatorParamKind::Float,
    required: false,
    default: Some("0.02"),
    description: "Acceleration factor increment",
    min: Some(0.0),
    max: None,
};

const P_AF_MAX_02: IndicatorParamMeta = IndicatorParamMeta {
    name: "af_max",
    kind: IndicatorParamKind::Float,
    required: false,
    default: Some("0.2"),
    description: "Maximum acceleration factor",
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
    optional_fields: &[],
    lookback_params: &[],
    default_lookback: Some(2),
    warmup_policy: "none",
};

const STYLE_PRIMARY_LINE: &[StyleSlotMeta] = &[StyleSlotMeta {
    slot: "primary_line",
    kind: StyleSlotType::Stroke,
    default: StyleDefaultMeta {
        color: "#38bdf8",
        width: Some(1.5),
        opacity: None,
        pattern: Some(StrokePattern::Solid),
    },
}];
const STYLE_VOLUME_HIST: &[StyleSlotMeta] = &[StyleSlotMeta {
    slot: "volume_hist",
    kind: StyleSlotType::Fill,
    default: StyleDefaultMeta {
        color: "#94a3b8",
        width: None,
        opacity: Some(0.8),
        pattern: None,
    },
}];
const STYLE_SIGNAL_MARKER: &[StyleSlotMeta] = &[StyleSlotMeta {
    slot: "signal_marker",
    kind: StyleSlotType::Stroke,
    default: StyleDefaultMeta {
        color: "#ef4444",
        width: Some(1.0),
        opacity: None,
        pattern: Some(StrokePattern::Solid),
    },
}];
const STYLE_PRIMARY_SECONDARY: &[StyleSlotMeta] = &[
    StyleSlotMeta {
        slot: "primary_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#38bdf8",
            width: Some(1.5),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "secondary_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#f97316",
            width: Some(1.5),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
];
const STYLE_LINE_SIGNAL: &[StyleSlotMeta] = &[
    StyleSlotMeta {
        slot: "primary_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#38bdf8",
            width: Some(1.5),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "signal_marker",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#ef4444",
            width: Some(1.0),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
];

const VIS_PRICE_LINE_OUTPUTS: &[OutputVisualMeta] = &[OutputVisualMeta {
    output: "result",
    primitive: OutputVisualPrimitive::Line,
    style_slot: "primary_line",
    z_index: 30,
}];
const VIS_OSC_LINE_OUTPUTS: &[OutputVisualMeta] = &[OutputVisualMeta {
    output: "result",
    primitive: OutputVisualPrimitive::Line,
    style_slot: "primary_line",
    z_index: 30,
}];
const VIS_VOLUME_LINE_OUTPUTS: &[OutputVisualMeta] = &[OutputVisualMeta {
    output: "result",
    primitive: OutputVisualPrimitive::Line,
    style_slot: "primary_line",
    z_index: 30,
}];
const VIS_VOLUME_HIST_OUTPUTS: &[OutputVisualMeta] = &[OutputVisualMeta {
    output: "result",
    primitive: OutputVisualPrimitive::Histogram,
    style_slot: "volume_hist",
    z_index: 25,
}];
const VIS_SIGNAL_OUTPUTS: &[OutputVisualMeta] = &[OutputVisualMeta {
    output: "result",
    primitive: OutputVisualPrimitive::SignalFlag,
    style_slot: "signal_marker",
    z_index: 50,
}];

const VIS_PRICE_LINE: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::PriceOverlay,
    scale_group: IndicatorScaleGroup::Price,
    output_visuals: VIS_PRICE_LINE_OUTPUTS,
    style_slots: STYLE_PRIMARY_LINE,
};
const VIS_OSC_LINE: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Oscillator,
    output_visuals: VIS_OSC_LINE_OUTPUTS,
    style_slots: STYLE_PRIMARY_LINE,
};
const VIS_VOLUME_LINE: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Volume,
    output_visuals: VIS_VOLUME_LINE_OUTPUTS,
    style_slots: STYLE_PRIMARY_LINE,
};
const VIS_VOLUME_HIST: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Volume,
    output_visuals: VIS_VOLUME_HIST_OUTPUTS,
    style_slots: STYLE_VOLUME_HIST,
};
const VIS_SIGNAL_FLAG: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::PriceOverlay,
    scale_group: IndicatorScaleGroup::Binary,
    output_visuals: VIS_SIGNAL_OUTPUTS,
    style_slots: STYLE_SIGNAL_MARKER,
};
const STYLE_BBANDS: &[StyleSlotMeta] = &[
    StyleSlotMeta {
        slot: "upper_stroke",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#38bdf8",
            width: Some(1.25),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "lower_stroke",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#38bdf8",
            width: Some(1.25),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "middle_stroke",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#93c5fd",
            width: Some(1.25),
            opacity: None,
            pattern: Some(StrokePattern::Dashed),
        },
    },
    StyleSlotMeta {
        slot: "channel_fill",
        kind: StyleSlotType::Fill,
        default: StyleDefaultMeta {
            color: "#38bdf8",
            width: None,
            opacity: Some(0.15),
            pattern: None,
        },
    },
];
const VIS_BBANDS_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "upper",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "upper_stroke",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "lower",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "lower_stroke",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "upper|lower",
        primitive: OutputVisualPrimitive::BandFill,
        style_slot: "channel_fill",
        z_index: 20,
    },
    OutputVisualMeta {
        output: "middle",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "middle_stroke",
        z_index: 31,
    },
];
const VIS_BBANDS: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::PriceOverlay,
    scale_group: IndicatorScaleGroup::Price,
    output_visuals: VIS_BBANDS_OUTPUTS,
    style_slots: STYLE_BBANDS,
};
const STYLE_MACD: &[StyleSlotMeta] = &[
    StyleSlotMeta {
        slot: "macd_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#38bdf8",
            width: Some(1.5),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "signal_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#f97316",
            width: Some(1.25),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "histogram_fill",
        kind: StyleSlotType::Fill,
        default: StyleDefaultMeta {
            color: "#94a3b8",
            width: None,
            opacity: Some(0.7),
            pattern: None,
        },
    },
];
const VIS_MACD_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "macd",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "macd_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "signal",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "signal_line",
        z_index: 31,
    },
    OutputVisualMeta {
        output: "histogram",
        primitive: OutputVisualPrimitive::Histogram,
        style_slot: "histogram_fill",
        z_index: 20,
    },
];
const VIS_MACD: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Oscillator,
    output_visuals: VIS_MACD_OUTPUTS,
    style_slots: STYLE_MACD,
};
const STYLE_ADX: &[StyleSlotMeta] = &[
    StyleSlotMeta {
        slot: "adx_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#38bdf8",
            width: Some(1.5),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "plus_di_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#22c55e",
            width: Some(1.0),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "minus_di_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#ef4444",
            width: Some(1.0),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
];
const VIS_ADX_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "adx",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "adx_line",
        z_index: 31,
    },
    OutputVisualMeta {
        output: "plus_di",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "plus_di_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "minus_di",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "minus_di_line",
        z_index: 30,
    },
];
const VIS_ADX: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Oscillator,
    output_visuals: VIS_ADX_OUTPUTS,
    style_slots: STYLE_ADX,
};
const VIS_STOCHASTIC_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "k",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "primary_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "d",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "secondary_line",
        z_index: 31,
    },
];
const VIS_STOCHASTIC: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Oscillator,
    output_visuals: VIS_STOCHASTIC_OUTPUTS,
    style_slots: STYLE_PRIMARY_SECONDARY,
};
const VIS_VORTEX_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "plus",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "primary_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "minus",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "secondary_line",
        z_index: 31,
    },
];
const VIS_VORTEX: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Oscillator,
    output_visuals: VIS_VORTEX_OUTPUTS,
    style_slots: STYLE_PRIMARY_SECONDARY,
};
const VIS_ICHIMOKU_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "tenkan_sen",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "tenkan_line",
        z_index: 33,
    },
    OutputVisualMeta {
        output: "kijun_sen",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "kijun_line",
        z_index: 32,
    },
    OutputVisualMeta {
        output: "senkou_span_a",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "senkou_a_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "senkou_span_b",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "senkou_b_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "senkou_span_a|senkou_span_b",
        primitive: OutputVisualPrimitive::BandFill,
        style_slot: "kumo_fill",
        z_index: 20,
    },
    OutputVisualMeta {
        output: "chikou_span",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "chikou_line",
        z_index: 31,
    },
];
const STYLE_ICHIMOKU: &[StyleSlotMeta] = &[
    StyleSlotMeta {
        slot: "tenkan_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#f97316",
            width: Some(1.2),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "kijun_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#3b82f6",
            width: Some(1.2),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "senkou_a_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#22c55e",
            width: Some(1.0),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "senkou_b_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#ef4444",
            width: Some(1.0),
            opacity: None,
            pattern: Some(StrokePattern::Solid),
        },
    },
    StyleSlotMeta {
        slot: "kumo_fill",
        kind: StyleSlotType::Fill,
        default: StyleDefaultMeta {
            color: "#64748b",
            width: None,
            opacity: Some(0.15),
            pattern: None,
        },
    },
    StyleSlotMeta {
        slot: "chikou_line",
        kind: StyleSlotType::Stroke,
        default: StyleDefaultMeta {
            color: "#a855f7",
            width: Some(1.0),
            opacity: None,
            pattern: Some(StrokePattern::Dashed),
        },
    },
];
const VIS_ICHIMOKU: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::PriceOverlay,
    scale_group: IndicatorScaleGroup::Price,
    output_visuals: VIS_ICHIMOKU_OUTPUTS,
    style_slots: STYLE_ICHIMOKU,
};
const VIS_FISHER_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "fisher",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "primary_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "signal",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "secondary_line",
        z_index: 31,
    },
];
const VIS_FISHER: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Oscillator,
    output_visuals: VIS_FISHER_OUTPUTS,
    style_slots: STYLE_PRIMARY_SECONDARY,
};
const VIS_ELDER_RAY_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "bull",
        primitive: OutputVisualPrimitive::Histogram,
        style_slot: "primary_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "bear",
        primitive: OutputVisualPrimitive::Histogram,
        style_slot: "secondary_line",
        z_index: 30,
    },
];
const VIS_ELDER_RAY: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::SeparatePane,
    scale_group: IndicatorScaleGroup::Oscillator,
    output_visuals: VIS_ELDER_RAY_OUTPUTS,
    style_slots: STYLE_PRIMARY_SECONDARY,
};
const VIS_LINE_SIGNAL_PSAR_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "sar",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "primary_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "direction",
        primitive: OutputVisualPrimitive::SignalFlag,
        style_slot: "signal_marker",
        z_index: 40,
    },
];
const VIS_PSAR: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::PriceOverlay,
    scale_group: IndicatorScaleGroup::Price,
    output_visuals: VIS_LINE_SIGNAL_PSAR_OUTPUTS,
    style_slots: STYLE_LINE_SIGNAL,
};
const VIS_LINE_SIGNAL_SUPERTREND_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "supertrend",
        primitive: OutputVisualPrimitive::Line,
        style_slot: "primary_line",
        z_index: 30,
    },
    OutputVisualMeta {
        output: "direction",
        primitive: OutputVisualPrimitive::SignalFlag,
        style_slot: "signal_marker",
        z_index: 40,
    },
];
const VIS_SUPERTREND: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::PriceOverlay,
    scale_group: IndicatorScaleGroup::Price,
    output_visuals: VIS_LINE_SIGNAL_SUPERTREND_OUTPUTS,
    style_slots: STYLE_LINE_SIGNAL,
};
const VIS_SWING_POINTS_OUTPUTS: &[OutputVisualMeta] = &[
    OutputVisualMeta {
        output: "swing_high",
        primitive: OutputVisualPrimitive::SignalFlag,
        style_slot: "signal_marker",
        z_index: 50,
    },
    OutputVisualMeta {
        output: "swing_low",
        primitive: OutputVisualPrimitive::SignalFlag,
        style_slot: "signal_marker",
        z_index: 50,
    },
];
const VIS_SWING_POINTS: IndicatorVisualMeta = IndicatorVisualMeta {
    pane_hint: IndicatorPaneHint::PriceOverlay,
    scale_group: IndicatorScaleGroup::Binary,
    output_visuals: VIS_SWING_POINTS_OUTPUTS,
    style_slots: STYLE_SIGNAL_MARKER,
};

mod event;
mod momentum;
mod pattern;
mod trend;
mod volatility;
mod volume;

/// Returns the canonical indicator catalog exposed by Rust compute.
pub fn indicator_catalog() -> &'static [IndicatorMeta] {
    use std::sync::OnceLock;

    static CATALOG: OnceLock<Box<[IndicatorMeta]>> = OnceLock::new();
    CATALOG
        .get_or_init(|| {
            let mut catalog = Vec::new();
            catalog.extend_from_slice(trend::ENTRIES);
            catalog.extend_from_slice(momentum::ENTRIES);
            catalog.extend_from_slice(volatility::ENTRIES);
            catalog.extend_from_slice(volume::ENTRIES);
            catalog.extend_from_slice(event::ENTRIES);
            catalog.extend_from_slice(pattern::ENTRIES);
            catalog.sort_by(|a, b| a.id.cmp(b.id));
            catalog.into_boxed_slice()
        })
        .as_ref()
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
