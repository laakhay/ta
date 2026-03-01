use super::*;

mod cross;
mod crossdown;
mod crossup;
mod enter;
mod exit;
mod falling;
mod falling_pct;
mod in_channel;
mod out;
mod rising;
mod rising_pct;

pub const ENTRIES: &[IndicatorMeta] = &[
    cross::META,
    crossdown::META,
    crossup::META,
    enter::META,
    exit::META,
    falling::META,
    falling_pct::META,
    in_channel::META,
    out::META,
    rising::META,
    rising_pct::META,
];
