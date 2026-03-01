use super::*;

mod adx;
mod elder_ray;
mod ema;
mod fisher;
mod hma;
mod ichimoku;
mod macd;
mod psar;
mod sma;
mod supertrend;
mod wma;

pub const ENTRIES: &[IndicatorMeta] = &[
    adx::META,
    elder_ray::META,
    ema::META,
    fisher::META,
    hma::META,
    ichimoku::META,
    macd::META,
    psar::META,
    sma::META,
    supertrend::META,
    wma::META,
];
