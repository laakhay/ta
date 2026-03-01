use super::*;

mod ao;
mod cci;
mod cmo;
mod coppock;
mod mfi;
mod roc;
mod rsi;
mod stochastic;
mod vortex;
mod williams_r;

pub const ENTRIES: &[IndicatorMeta] = &[
    ao::META,
    cci::META,
    cmo::META,
    coppock::META,
    mfi::META,
    roc::META,
    rsi::META,
    stochastic::META,
    vortex::META,
    williams_r::META,
];
