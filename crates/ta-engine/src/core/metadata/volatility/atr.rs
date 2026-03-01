use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
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
};
