# Mean Reversion Backtest Compatibility (Laakhay-TA vs Current Service)

This note compares the existing FastAPI backtest flow (excerpted from
`run_mean_reversion_backtest`) with what a Laakhay-TA powered implementation
would need. The goal is to identify feature gaps, required integrations, and
possible migration paths.

## 1. Current Service Responsibilities

The existing endpoint performs several tasks:

1. **Data Acquisition**
   - Pulls 1h OHLCV and 5m OHLCV from Binance via `get_klines`.
   - Ensures the result is sorted and index-aligned.

2. **Stateful Mean Reversion Tracker**
   - Instantiates `MeanReversionTracker`, which internally maintains:
     - `hourly_tracker` for swing highs/lows, retracement levels, SMA, etc.
     - Streaming updates via `process_hourly_candle` and `process_five_min_candle`.
     - A notion of “current swing legs”, “retracement zones”, and trade setups with
       full status history.
   - Keeps dictionaries of interest points, retracements, and setups keyed by indices.

3. **Event Serialization**
   - Converts internal tracker data (swing points, retracements, setups) into rich
     Pydantic models for API responses.
   - Captures validity windows (`valid_from`, `valid_till`) and various metadata
     unknown to Laakhay-TA today (trade result, monitoring status, drawdown, etc.).

4. **Multi-Timeframe Execution**
   - Hourly bars drive structure.
   - 5-minute bars feed execution-level decisions (e.g., order fills, trailing info).

5. **Risk/Reward, SL/TP, Setup Status**
   - Tracker computes zones (0.618/0.65/0.75), stop-loss, target, entry/exit events.
   - Maintains state transitions (monitoring, invalidated, completed, etc.).

## 2. Laakhay-TA Capabilities Today

| Requirement                               | Status in Laakhay-TA                                  |
|-------------------------------------------|--------------------------------------------------------|
| Series primitives (rolling, sync, etc.)   | ✅ Already implemented                                 |
| Swing detection                           | ✅ `swing_points`, `swing_highs`, `swing_lows`          |
| Fibonacci retracement levels              | ✅ `fib_retracement` (stateless, uses swing anchors)    |
| Immutable dataset / multi-timeframe       | ✅ `Dataset`, `sync_timeframe`, `downsample/upsample`   |
| Expression composition & evaluation       | ✅ Engine supports deriving signals/flags               |
| Streaming updates                         | ⚠️ Requires custom loop (Dataset updates + re-eval)     |
| Trade setup state machine                 | ❌ Not provided (no strategy/stateful tracker yet)      |
| Risk/reward handling, SL/TP management    | ❌ Needs explicit strategy/backtest module              |
| Consolidated backtest metrics/output      | ❌ Pending future `ta.strategy` roadmap                 |
| Rich event serialization                  | ❌ Would need a layer on top of expression outputs      |

## 3. Compatibility Assessment

### What Maps Directly
- **Swing structure**: `MeanReversionTracker.hourly_tracker.swing_highs/lows`
  can be replaced with `swing_points` / `swing_highs` / `swing_lows` indicators.
- **Fibonacci zones**: `fib_retracement` computes the same `0.618/0.650/0.750`
  lines without mutating state. Availability masks show when each zone is live.
- **SMA / other indicators**: Already present via existing primitives.
- **Multi-timeframe alignment**: Use `Dataset` with 4h, 1h, 5m entries and
  `sync_timeframe` to project higher timeframe signals downward.

### What Needs Additional Work
- **Stateful tracking of swings**:
  - The current code tracks validity windows (`valid_from`, `valid_till`), which depend
    on when future bars confirm or invalidate a swing.
  - We can reproduce these windows with expression+post-processing (walk the boolean
    swing flag to mark activation ranges), but it’s not built-in yet.
- **Retracement objects (`RetracementData`)**:
  - Today’s tracker pairs swing start/end indices and stores direction plus a dict of
    levels. In Laakhay-TA, `fib_retracement` outputs series; you’d need a small adapter
    to convert transitions in the availability mask into these discrete objects.
- **Setups and status history**:
  - The tracker maintains per-leg structures with monitoring/invalidation/filled states.
  - Laakhay-TA currently lacks a stateful strategy module; implementing something similar
    requires either:
      1. Extending the upcoming `ta.strategy` package (on the roadmap) to support these
         workflow states; or
      2. Building an external state machine that consumes indicator outputs.
- **Streaming loops**:
  - The existing service processes bars incrementally; Laakhay-TA is stateless. You can
    mimic the stream by incrementally appending to a `Dataset` and re-running expressions,
    but you still need a tracker to store cross-bar state (e.g., the current setup being
    monitored).
- **API response models**:
  - The current shape (with nested dataclasses) is highly specific. A Laakhay-TA version
    would either:
      - Emit raw series and let the frontend derive structures; or
      - Post-process indicator outputs into the same shapes (requires custom code).

## 4. Migration Strategy

1. **Replace Swing & Fib Calculations**
   - Swap `MeanReversionTracker`’s swing/fib logic with calls to Laakhay-TA indicators.
   - Use availability masks to detect when a swing point is confirmed and build the same
     metadata (valid_from, valid_till).

2. **Introduce Expression-Based Signals**
   - Implement the entry criteria using `Expression` (e.g., `between(level_618, level_50)`).
   - Evaluate these expressions per bar to emulate the tracker's monitoring behavior.

3. **Stateful Wrapper for Trade Management**
   - Until `ta.strategy` is ready, write a thin state machine that:
     - Listens for entry signal transitions (`False → True`).
     - Records entry price, sets SL/TP via indicator outputs (`level_75`, etc.).
     - Tracks drawdown and status history (mirroring `MeanReversionTracker` fields).

4. **Backtest Execution**
   - Use a simple vectorized loop or incremental evaluation over the dataset.
   - Capture trades in a structure similar to `SetupData`.
   - Optionally reuse Pandas-based PnL calculation or integrate with a third-party engine.

5. **Serialization Layer**
   - Convert the Laakhay-TA outputs + state machine results into the existing Pydantic
     response models to maintain API compatibility.

## 5. Open Questions / Roadmap Alignment

| Feature                          | Path Forward                                             |
|----------------------------------|----------------------------------------------------------|
| Strategy/backtest module         | Align with `ta.strategy` when it lands.                  |
| Streaming updates                | Provide examples/utility for incremental dataset updates.|
| Event serialization              | Consider a helper to convert Series + masks to “events”. |
| Risk management utilities        | Potential additions to the roadmap (`stop`, `target`).   |

## 6. Conclusion

Laakhay-TA already covers the stateless technical analysis primitives required
by the current mean-reversion tracker (swings, fibs, SMA, multi-timeframe sync).
To fully replicate the existing service, two major additions are needed:

1. A **stateful orchestration layer** (pending `ta.strategy` or custom state machine).  
   The new `Stream` helper (`laakhay.ta.stream.Stream`) handles dataset appends and
   availability transitions, but trade bookkeeping remains an external concern.
2. A **serialization bridge** that converts indicator outputs into the rich response
   models expected by the API.

With those layers in place, the core analytics can be powered entirely by Laakhay-TA
without changing the external behavior of the backtest endpoint.
