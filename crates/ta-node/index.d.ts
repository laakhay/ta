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

export function sma(values: number[], period: number): number[];
export function ema(values: number[], period: number): number[];
export function wma(values: number[], period: number): number[];
export function hma(values: number[], period: number): number[];
export function rsi(values: number[], period: number): number[];
export function roc(values: number[], period: number): number[];
export function cmo(values: number[], period: number): number[];
export function macd(
  values: number[],
  fastPeriod: number,
  slowPeriod: number,
  signalPeriod: number,
): MacdOutput;
export function bbands(values: number[], period: number, stdDev: number): BbandsOutput;
