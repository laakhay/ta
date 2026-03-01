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

export interface TaNodeBindings {
  engineVersion(): string;
  sma(values: number[], period: number): number[];
  ema(values: number[], period: number): number[];
  rma(values: number[], period: number): number[];
  wma(values: number[], period: number): number[];
  hma(values: number[], period: number): number[];
  rsi(values: number[], period: number): number[];
  roc(values: number[], period: number): number[];
  cmo(values: number[], period: number): number[];
  ao(high: number[], low: number[], fastPeriod: number, slowPeriod: number): number[];
  coppock(values: number[], wmaPeriod: number, fastRoc: number, slowRoc: number): number[];
  williamsR(high: number[], low: number[], close: number[], period: number): number[];
  mfi(high: number[], low: number[], close: number[], volume: number[], period: number): number[];
  cci(high: number[], low: number[], close: number[], period: number): number[];
  atr(high: number[], low: number[], close: number[], period: number): number[];
  atrFromTr(values: number[], period: number): number[];
  obv(close: number[], volume: number[]): number[];
  vwap(high: number[], low: number[], close: number[], volume: number[]): number[];
  cmf(high: number[], low: number[], close: number[], volume: number[], period: number): number[];
  klingerVf(high: number[], low: number[], close: number[], volume: number[]): number[];
  macd(values: number[], fastPeriod: number, slowPeriod: number, signalPeriod: number): MacdOutput;
  bbands(values: number[], period: number, stdDev: number): BbandsOutput;
  stochastic(
    high: number[],
    low: number[],
    close: number[],
    kPeriod: number,
    dPeriod: number,
    smooth: number,
  ): StochasticOutput;
  adx(high: number[], low: number[], close: number[], period: number): AdxOutput;
  ichimoku(
    high: number[],
    low: number[],
    close: number[],
    tenkanPeriod: number,
    kijunPeriod: number,
    spanBPeriod: number,
    displacement: number,
  ): IchimokuOutput;
  supertrend(
    high: number[],
    low: number[],
    close: number[],
    period: number,
    multiplier: number,
  ): SupertrendOutput;
  psar(
    high: number[],
    low: number[],
    close: number[],
    afStart: number,
    afIncrement: number,
    afMax: number,
  ): PsarOutput;
  swingPointsRaw(
    high: number[],
    low: number[],
    left: number,
    right: number,
    allowEqualExtremes: boolean,
  ): SwingPointsOutput;
  vortex(high: number[], low: number[], close: number[], period: number): VortexOutput;
  elderRay(high: number[], low: number[], close: number[], period: number): ElderRayOutput;
  fisher(high: number[], low: number[], period: number): FisherOutput;
  donchian(high: number[], low: number[], period: number): DonchianOutput;
  keltner(
    high: number[],
    low: number[],
    close: number[],
    emaPeriod: number,
    atrPeriod: number,
    multiplier: number,
  ): KeltnerOutput;
  klinger(
    high: number[],
    low: number[],
    close: number[],
    volume: number[],
    fastPeriod: number,
    slowPeriod: number,
    signalPeriod: number,
  ): KlingerOutput;
}

let cached: TaNodeBindings | null = null;

export function setNativeBindingsForTest(bindings: TaNodeBindings | null): void {
  cached = bindings;
}

export function getNativeBindings(): TaNodeBindings {
  if (cached) {
    return cached;
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const native = require("@laakhay/ta-node") as TaNodeBindings;
    cached = native;
    return native;
  } catch (error) {
    throw new Error(
      `Unable to load @laakhay/ta-node native bindings. Build/install ta-node first. Original error: ${String(error)}`,
    );
  }
}
