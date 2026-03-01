use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
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
    visual: VIS_PRICE_LINE,
    runtime_binding: "roc",
};
