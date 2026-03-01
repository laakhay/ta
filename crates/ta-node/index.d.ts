export function engineVersion(): string;

export interface MacdOutput {
  macd: number[];
  signal: number[];
  histogram: number[];
}

export interface BbandsOutput {
  upper: number[];
  middle: number[];
  lower: number[];
}

export interface StochasticOutput {
  k: number[];
  d: number[];
}

export interface AdxOutput {
  adx: number[];
  plus_di: number[];
  minus_di: number[];
}

export interface IchimokuOutput {
  tenkan_sen: number[];
  kijun_sen: number[];
  senkou_span_a: number[];
  senkou_span_b: number[];
  chikou_span: number[];
}

export interface SupertrendOutput {
  supertrend: number[];
  direction: number[];
}

export interface PsarOutput {
  sar: number[];
  direction: number[];
}

export interface SwingPointsOutput {
  swing_high: boolean[];
  swing_low: boolean[];
}

export interface VortexOutput {
  plus: number[];
  minus: number[];
}

export interface ElderRayOutput {
  bull: number[];
  bear: number[];
}

export interface FisherOutput {
  fisher: number[];
  signal: number[];
}

export interface DonchianOutput {
  upper: number[];
  lower: number[];
  middle: number[];
}

export interface KeltnerOutput {
  upper: number[];
  middle: number[];
  lower: number[];
}

export interface KlingerOutput {
  klinger: number[];
  signal: number[];
}

export function sma(values: number[], period: number): number[];
export function ema(values: number[], period: number): number[];
export function rma(values: number[], period: number): number[];
export function wma(values: number[], period: number): number[];
export function hma(values: number[], period: number): number[];
export function rsi(values: number[], period: number): number[];
export function roc(values: number[], period: number): number[];
export function cmo(values: number[], period: number): number[];

export function ao(high: number[], low: number[], fastPeriod: number, slowPeriod: number): number[];
export function coppock(values: number[], wmaPeriod: number, fastRoc: number, slowRoc: number): number[];
export function williamsR(high: number[], low: number[], close: number[], period: number): number[];
export function mfi(high: number[], low: number[], close: number[], volume: number[], period: number): number[];
export function cci(high: number[], low: number[], close: number[], period: number): number[];

export function atr(high: number[], low: number[], close: number[], period: number): number[];
export function atrFromTr(values: number[], period: number): number[];

export function obv(close: number[], volume: number[]): number[];
export function vwap(high: number[], low: number[], close: number[], volume: number[]): number[];
export function cmf(high: number[], low: number[], close: number[], volume: number[], period: number): number[];
export function klingerVf(high: number[], low: number[], close: number[], volume: number[]): number[];

export function macd(values: number[], fastPeriod: number, slowPeriod: number, signalPeriod: number): MacdOutput;
export function bbands(values: number[], period: number, stdDev: number): BbandsOutput;
export function stochastic(
  high: number[],
  low: number[],
  close: number[],
  kPeriod: number,
  dPeriod: number,
  smooth: number,
): StochasticOutput;
export function adx(high: number[], low: number[], close: number[], period: number): AdxOutput;
export function ichimoku(
  high: number[],
  low: number[],
  close: number[],
  tenkanPeriod: number,
  kijunPeriod: number,
  spanBPeriod: number,
  displacement: number,
): IchimokuOutput;
export function supertrend(
  high: number[],
  low: number[],
  close: number[],
  period: number,
  multiplier: number,
): SupertrendOutput;
export function psar(
  high: number[],
  low: number[],
  close: number[],
  afStart: number,
  afIncrement: number,
  afMax: number,
): PsarOutput;
export function swingPointsRaw(
  high: number[],
  low: number[],
  left: number,
  right: number,
  allowEqualExtremes: boolean,
): SwingPointsOutput;
export function vortex(high: number[], low: number[], close: number[], period: number): VortexOutput;
export function elderRay(high: number[], low: number[], close: number[], period: number): ElderRayOutput;
export function fisher(high: number[], low: number[], period: number): FisherOutput;
export function donchian(high: number[], low: number[], period: number): DonchianOutput;
export function keltner(
  high: number[],
  low: number[],
  close: number[],
  emaPeriod: number,
  atrPeriod: number,
  multiplier: number,
): KeltnerOutput;
export function klinger(
  high: number[],
  low: number[],
  close: number[],
  volume: number[],
  fastPeriod: number,
  slowPeriod: number,
  signalPeriod: number,
): KlingerOutput;
