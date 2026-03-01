import {
  type AdxOutput,
  type BbandsOutput,
  type DonchianOutput,
  type ElderRayOutput,
  type FisherOutput,
  type IchimokuOutput,
  type KeltnerOutput,
  type KlingerOutput,
  type MacdOutput,
  type PsarOutput,
  type StochasticOutput,
  type SupertrendOutput,
  type SwingPointsOutput,
  type VortexOutput,
  getNativeBindings,
} from "./native";

export type {
  AdxOutput,
  BbandsOutput,
  DonchianOutput,
  ElderRayOutput,
  FisherOutput,
  IchimokuOutput,
  KeltnerOutput,
  KlingerOutput,
  MacdOutput,
  PsarOutput,
  StochasticOutput,
  SupertrendOutput,
  SwingPointsOutput,
  VortexOutput,
} from "./native";

export function engineVersion(): string {
  return getNativeBindings().engineVersion();
}

export function sma(values: number[], period: number): number[] {
  return getNativeBindings().sma(values, period);
}

export function ema(values: number[], period: number): number[] {
  return getNativeBindings().ema(values, period);
}

export function rma(values: number[], period: number): number[] {
  return getNativeBindings().rma(values, period);
}

export function wma(values: number[], period: number): number[] {
  return getNativeBindings().wma(values, period);
}

export function hma(values: number[], period: number): number[] {
  return getNativeBindings().hma(values, period);
}

export function rsi(values: number[], period: number): number[] {
  return getNativeBindings().rsi(values, period);
}

export function roc(values: number[], period: number): number[] {
  return getNativeBindings().roc(values, period);
}

export function cmo(values: number[], period: number): number[] {
  return getNativeBindings().cmo(values, period);
}

export function ao(high: number[], low: number[], fastPeriod: number, slowPeriod: number): number[] {
  return getNativeBindings().ao(high, low, fastPeriod, slowPeriod);
}

export function coppock(values: number[], wmaPeriod: number, fastRoc: number, slowRoc: number): number[] {
  return getNativeBindings().coppock(values, wmaPeriod, fastRoc, slowRoc);
}

export function williamsR(high: number[], low: number[], close: number[], period: number): number[] {
  return getNativeBindings().williamsR(high, low, close, period);
}

export function mfi(high: number[], low: number[], close: number[], volume: number[], period: number): number[] {
  return getNativeBindings().mfi(high, low, close, volume, period);
}

export function cci(high: number[], low: number[], close: number[], period: number): number[] {
  return getNativeBindings().cci(high, low, close, period);
}

export function atr(high: number[], low: number[], close: number[], period: number): number[] {
  return getNativeBindings().atr(high, low, close, period);
}

export function atrFromTr(values: number[], period: number): number[] {
  return getNativeBindings().atrFromTr(values, period);
}

export function obv(close: number[], volume: number[]): number[] {
  return getNativeBindings().obv(close, volume);
}

export function vwap(high: number[], low: number[], close: number[], volume: number[]): number[] {
  return getNativeBindings().vwap(high, low, close, volume);
}

export function cmf(high: number[], low: number[], close: number[], volume: number[], period: number): number[] {
  return getNativeBindings().cmf(high, low, close, volume, period);
}

export function klingerVf(high: number[], low: number[], close: number[], volume: number[]): number[] {
  return getNativeBindings().klingerVf(high, low, close, volume);
}

export function macd(values: number[], fastPeriod: number, slowPeriod: number, signalPeriod: number): MacdOutput {
  return getNativeBindings().macd(values, fastPeriod, slowPeriod, signalPeriod);
}

export function bbands(values: number[], period: number, stdDev: number): BbandsOutput {
  return getNativeBindings().bbands(values, period, stdDev);
}

export function stochastic(
  high: number[],
  low: number[],
  close: number[],
  kPeriod: number,
  dPeriod: number,
  smooth: number,
): StochasticOutput {
  return getNativeBindings().stochastic(high, low, close, kPeriod, dPeriod, smooth);
}

export function adx(high: number[], low: number[], close: number[], period: number): AdxOutput {
  return getNativeBindings().adx(high, low, close, period);
}

export function ichimoku(
  high: number[],
  low: number[],
  close: number[],
  tenkanPeriod: number,
  kijunPeriod: number,
  spanBPeriod: number,
  displacement: number,
): IchimokuOutput {
  return getNativeBindings().ichimoku(
    high,
    low,
    close,
    tenkanPeriod,
    kijunPeriod,
    spanBPeriod,
    displacement,
  );
}

export function supertrend(
  high: number[],
  low: number[],
  close: number[],
  period: number,
  multiplier: number,
): SupertrendOutput {
  return getNativeBindings().supertrend(high, low, close, period, multiplier);
}

export function psar(
  high: number[],
  low: number[],
  close: number[],
  afStart: number,
  afIncrement: number,
  afMax: number,
): PsarOutput {
  return getNativeBindings().psar(high, low, close, afStart, afIncrement, afMax);
}

export function swingPointsRaw(
  high: number[],
  low: number[],
  left: number,
  right: number,
  allowEqualExtremes: boolean,
): SwingPointsOutput {
  return getNativeBindings().swingPointsRaw(high, low, left, right, allowEqualExtremes);
}

export function vortex(high: number[], low: number[], close: number[], period: number): VortexOutput {
  return getNativeBindings().vortex(high, low, close, period);
}

export function elderRay(high: number[], low: number[], close: number[], period: number): ElderRayOutput {
  return getNativeBindings().elderRay(high, low, close, period);
}

export function fisher(high: number[], low: number[], period: number): FisherOutput {
  return getNativeBindings().fisher(high, low, period);
}

export function donchian(high: number[], low: number[], period: number): DonchianOutput {
  return getNativeBindings().donchian(high, low, period);
}

export function keltner(
  high: number[],
  low: number[],
  close: number[],
  emaPeriod: number,
  atrPeriod: number,
  multiplier: number,
): KeltnerOutput {
  return getNativeBindings().keltner(high, low, close, emaPeriod, atrPeriod, multiplier);
}

export function klinger(
  high: number[],
  low: number[],
  close: number[],
  volume: number[],
  fastPeriod: number,
  slowPeriod: number,
  signalPeriod: number,
): KlingerOutput {
  return getNativeBindings().klinger(high, low, close, volume, fastPeriod, slowPeriod, signalPeriod);
}
