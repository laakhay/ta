# Vision – Laakhay TA

Laakhay TA is a Rust-first technical analysis runtime with a Python ergonomics layer.

## Product Direction

1. **Rust owns compute** - indicator kernels, dataset operations, batch execution, and incremental execution run in Rust.
2. **Python owns ergonomics** - DSL authoring, expression composition, planner/orchestration, and developer experience stay in Python.
3. **Single runtime truth** - no long-term dual compute backends for the same indicator path.
4. **Deterministic execution** - snapshot/replay and parity tests enforce reproducible results.
5. **Adapter-first expansion** - Python today; FFI/Node and other runtimes should reuse the same Rust engine contracts.

## Architectural Intent

| Layer | Responsibility | Current Location |
|---|---|---|
| Engine Core | dataset handles, append/sync/downsample, contracts, metadata | `crates/ta-engine/src/core` |
| Indicators | canonical kernel implementations | `crates/ta-engine/src/indicators` |
| Execution Runtime | batch graph execution + incremental runtime | `crates/ta-engine/src/execution` |
| Python Binding | data marshaling + engine invocation | `crates/ta-py` |
| Python UX | DSL, expression graph, planning, package API | `python/src/laakhay` |
| Runtime Adapters | C ABI and future Node integration | `crates/ta-ffi`, `crates/ta-node` |

## Near-Term Goals

- Expand Rust indicator coverage until Python compute fallback is eliminated for core indicators.
- Keep planner/DSL in Python while executing graph compute in Rust.
- Add/expand cross-runtime parity and golden tests in repo-level `tests/`.
- Keep APIs explicit and inspectable (metadata/catalog remains first-class).

## Non-Goals (Current Phase)

- Backward compatibility guarantees while architecture is still converging.
- A fully Rust-native DSL before Rust execution coverage is complete.

## Success Criteria

- New indicator compute lands in Rust first.
- CI validates Python behavior and Rust behavior with parity checks.
- Python package remains ergonomic while avoiding hidden compute divergence from Rust.
