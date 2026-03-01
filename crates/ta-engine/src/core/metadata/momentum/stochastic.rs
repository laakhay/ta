use super::*;

pub const META: IndicatorMeta = IndicatorMeta {
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
    visual: VIS_STOCHASTIC,
    runtime_binding: "stochastic_kd",
};
