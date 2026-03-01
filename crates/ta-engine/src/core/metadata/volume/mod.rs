use super::*;

mod cmf;
mod klinger_vf;
mod obv;
mod vwap;

pub const ENTRIES: &[IndicatorMeta] = &[cmf::META, klinger_vf::META, obv::META, vwap::META];
