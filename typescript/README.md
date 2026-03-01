# laakhay-ta-ts

TypeScript direct-indicator module for `laakhay-ta`.

This package is intentionally thin: it forwards calls directly to `@laakhay/ta-node`.
No DSL/planner surface is provided.

## Install

```bash
cd typescript
npm install
```

You also need native bindings available:

```bash
# from repo root
cargo build -p ta-node
```

## Usage

```ts
import { sma, macd, bbands } from "laakhay-ta-ts";

const close = [1, 2, 3, 4, 5, 6];
const sma20 = sma(close, 20);
const m = macd(close, 12, 26, 9);
const b = bbands(close, 20, 2.0);
```

## Notes

- Runtime errors from native bindings are surfaced directly.
- Validation errors are stable (`ERR_PERIOD_INVALID`, `ERR_LENGTH_MISMATCH`).
