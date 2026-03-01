use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
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
    visual: VIS_OSC_LINE,
    runtime_binding: "cci",
};
