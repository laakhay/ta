# Golden Parity Fixtures

These fixtures anchor parity checks for the Rust-first runtime migration.

- `rolling_fixture_v1.json`: deterministic inputs/outputs for rolling and moving-average kernels.
- `momentum_volatility_fixture_v1.json`: deterministic inputs/outputs for RSI/ATR/Stochastic.

Update policy (beta):
1. Only update fixtures intentionally with a commit message explaining numerical behavior change.
2. Keep tolerances explicit in tests (do not silently broaden).
