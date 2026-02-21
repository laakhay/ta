# Laakhay Expression Engine Architecture

The `expr` module implements a high-performance, IR-centric engine for the definition and execution of technical analysis strategies. The system architecture is centered around a **Single Canonical Intermediate Representation (IR)**, which decouples the high-level syntax from the underlying execution logic.

## Core Architectural Philosophy

The engine is designed as a "Funnel." It accepts diverse inputs—such as Pythonic strings, operator-overloaded objects, or JSON blueprints—and normalizes them into a unified graph. This graph is then analyzed, optimized, and planned before being dispatched to a specialized execution environment.

### 1. Intermediate Representation (`ir/`)
The IR is the foundation of the library, providing a standardized, serializable format for all technical analysis logic. 
*   **`nodes.py`**: Implementation of the atomic nodes (`SourceRefNode`, `CallNode`, `BinaryOpNode`, `UnaryOpNode`). These nodes represent a pure, platform-independent description of a computation.
*   **`serialize.py`**: Provides the binary and string serialization layers. Because the IR is stable and platform-independent, an expression can be defined on a Python client and executed on a C++ or Rust backend with guaranteed parity.
*   **`types.py`**: Defines the type system used by the internal checker to differentiate between scalar values, series data, and multi-symbol datasets.

### 2. Frontend Translation Layers (`dsl/` & `algebra/`)
The Frontends are responsible for "Lifting" various representations into the IR world.
*   **`dsl/`**: Implements the **String-to-IR Translator**. It leverages Python's `ast` module to perform semantic analysis of string expressions. It includes a heuristic-based parser capable of resolving symbol shorthands (e.g., `BTC.USDT.price` to a `SourceRefNode`) and parameter mapping for indicator functions.
*   **`algebra/`**: Provides a **Fluent API** through operator overloading. By wrapping IR nodes in an `Expression` container, the library allows users to build complex logic using native Python operators (`+`, `-`, `>`, etc.). This layer handles automatic type coercion of Python literals (ints, floats) into `LiteralNode` wrappers.

### 3. Verification & Optimization (`typecheck/` & `normalize/`)
These modules act as a verification bridge between the Frontend and the Planner.
*   **`typecheck/`**: Performs static semantic validation. It ensures that indicators are receiving the correct input types (e.g., verifying that a moving average `period` is a scalar integer rather than a price series) and validates that the graph is free of circular dependencies.
*   **`normalize/`**: A transformation layer that rewrites the graph for performance. It performs algebraic simplifications, constant folding, and common subexpression elimination (CSE) to ensure the `Planner` receives the most efficient possible blueprint.

### 4. Strategy Planning (`planner/`)
The Planner is the "Brain" of the execution pipeline. It does not execute math directly; instead, it analyzes the IR graph to determine the resources required for evaluation.
*   **Data Requirements Extraction**: It walks the graph to identify every required data field (e.g., `ohlcv.close`, `trades.volume`).
*   **Lookback Calculation**: It computes the `min_lookback` for the entire strategy by aggregating the requirements of nested indicators. This allows the system to fetch the exact minimum amount of historical data needed for a successful calculation.
*   **Alignment Policy**: It determines how series with mismatched timestamps (e.g., a 1h series vs. a 15m series) should be joined and synchronized using the `AlignmentPolicy`.

### 5. Execution Runtime (`runtime/`)
The Runtime provides specialized environments for evaluating plans.
*   **`evaluator.py`**: The core execution engine. It processes the optimized graph, caching intermediate results (memoization) to ensure that shared sub-expressions are only calculated once.
*   **`preview.py`**: A low-latency runtime optimized for UI and exploration. It restricts evaluation to the most recent window of data, minimizing memory overhead and processing time for real-time dashboards.
*   **`engine.py`**: A minimal, one-off evaluation wrapper used for scripting and integration testing.

---

## The Execution Pipeline: End-to-End

When a developer executes a command like `expr.run(dataset)`, the following lifecycle occurs:

1.  **Parsing**: The input representation is converted to a raw IR graph.
2.  **Normalization**: The graph is optimized; redundant operations are merged, and constants are folded.
3.  **Type Checking**: The graph is validated for semantic and mathematical soundness.
4.  **Planning**: A `Plan` object is generated, detailing the minimal data set required and the execution order of the nodes.
5.  **Data Fetching**: The `Dataset` uses the requirements from the `Plan` to load the necessary series into the `SeriesContext`.
6.  **Evaluation**: The `Evaluator` walks the planned graph, executing the mathematical primitives on the provided data and caching intermediate series for reuse.
7.  **Emission**: The final result is returned as a typed `Series` or boolean signal.

## Future Extensibility

The architecture is designed to support future "Micro-Kernel" execution. By maintaining a strict boundary between the **IR** and the **Runtime**, the `Evaluator` can be swapped for alternatives (e.g., a GPU-accelerated engine or a localized streaming engine) without requiring any changes to the user's strategy definitions or parsing logic.
