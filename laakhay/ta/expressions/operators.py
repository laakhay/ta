"""Operator overloading for Series to enable expression building."""

from __future__ import annotations

from typing import Any

from ..core import Series
from ..core.dataset import Dataset
from .requirements import SignalRequirements, compute_requirements
from .models import BinaryOp, ExpressionNode, Literal, OperatorType, UnaryOp


class Expression:
    """Expression wrapper that enables operator overloading for Series objects."""

    def __init__(self, node: ExpressionNode):
        """Initialize expression with a node."""
        self._node = node

    def __add__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Addition operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.ADD, self._node, other_node))

    def __sub__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Subtraction operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.SUB, self._node, other_node))

    def __mul__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Multiplication operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MUL, self._node, other_node))

    def __truediv__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Division operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.DIV, self._node, other_node))

    def __mod__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Modulo operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MOD, self._node, other_node))

    def __pow__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Power operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.POW, self._node, other_node))

    def __eq__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        """Equality operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.EQ, self._node, other_node))

    def __ne__(self, other: Expression | Series[Any] | float | int) -> Expression:  # type: ignore[override]
        """Inequality operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.NE, self._node, other_node))

    def __lt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Less than operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LT, self._node, other_node))

    def __le__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Less than or equal operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.LE, self._node, other_node))

    def __gt__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Greater than operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GT, self._node, other_node))

    def __ge__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Greater than or equal operator."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.GE, self._node, other_node))

    def __neg__(self) -> Expression:
        """Unary negation operator."""
        return Expression(UnaryOp(OperatorType.NEG, self._node))

    def __pos__(self) -> Expression:
        """Unary plus operator."""
        return Expression(UnaryOp(OperatorType.POS, self._node))

    def __and__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Bitwise AND operator (logical AND)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.AND, self._node, other_node))

    def __or__(self, other: Expression | Series[Any] | float | int) -> Expression:
        """Bitwise OR operator (logical OR)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.OR, self._node, other_node))

    def __invert__(self) -> Expression:
        """Bitwise NOT operator (logical NOT)."""
        return Expression(UnaryOp(OperatorType.NOT, self._node))

    # Reverse operations for numeric literals
    def __radd__(self, other: float | int) -> Expression:
        """Reverse addition operator (other + self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.ADD, other_node, self._node))

    def __rsub__(self, other: float | int) -> Expression:
        """Reverse subtraction operator (other - self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.SUB, other_node, self._node))

    def __rmul__(self, other: float | int) -> Expression:
        """Reverse multiplication operator (other * self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MUL, other_node, self._node))

    def __rtruediv__(self, other: float | int) -> Expression:
        """Reverse division operator (other / self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.DIV, other_node, self._node))

    def __rmod__(self, other: float | int) -> Expression:
        """Reverse modulo operator (other % self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.MOD, other_node, self._node))

    def __rpow__(self, other: float | int) -> Expression:
        """Reverse power operator (other ** self)."""
        other_node = _to_node(other)
        return Expression(BinaryOp(OperatorType.POW, other_node, self._node))

    def evaluate(self, context: dict[str, Series[Any]]) -> Series[Any]:
        """Evaluate the expression with given context."""
        return self._node.evaluate(context)

    def dependencies(self) -> list[str]:
        """Get list of dependencies this expression requires."""
        return self._node.dependencies()

    def describe(self) -> str:
        """Get human-readable description of this expression with diagnostics."""
        base = self._node.describe()
        req = self.requirements()
        fields = ", ".join(f"{f.name}[{f.timeframe or '-'}]:{f.min_lookback}" for f in req.fields)
        derived = ", ".join(f"{d.name}({', '.join(f'{k}={v}' for k,v in d.params.items())})" for d in req.derived)
        parts = [f"expr: {base}"]
        if fields:
            parts.append(f"fields: {fields}")
        if derived:
            parts.append(f"derived: {derived}")
        return " | ".join(parts)

    def to_dot(self) -> str:
        """Return a Graphviz DOT representation of the expression graph.

        Note: No external dependency; returns a DOT string that can be rendered by graphviz tools.
        """
        from .models import BinaryOp, UnaryOp, Literal, ExpressionNode

        lines = ["digraph Expression {", "  rankdir=LR;"]
        node_ids: dict[int, str] = {}
        counter = 0

        def nid(n: ExpressionNode) -> str:
            nonlocal counter
            i = id(n)
            if i not in node_ids:
                node_ids[i] = f"n{counter}"
                counter += 1
            return node_ids[i]

        def label(n: ExpressionNode) -> str:
            t = type(n).__name__
            if isinstance(n, BinaryOp):
                return f"{t}\\n{n.operator.value}"
            if isinstance(n, UnaryOp):
                return f"{t}\\n{n.operator.value}"
            if isinstance(n, Literal):
                v = n.value
                if hasattr(v, 'symbol') and hasattr(v, 'timeframe'):
                    return f"Literal\\nSeries({getattr(v,'symbol','?')} {getattr(v,'timeframe','?')})"
                return f"Literal\\n{str(v)[:24]}"
            # Duck-typed IndicatorNode
            if n.__class__.__name__ == 'IndicatorNode' and hasattr(n, 'name'):
                return f"Indicator\\n{getattr(n,'name')}"
            return t

        edges: list[tuple[str, str]] = []

        def walk(n: ExpressionNode):
            me = nid(n)
            lines.append(f"  {me} [shape=box,label=\"{label(n)}\"];\n")
            if isinstance(n, BinaryOp):
                for child in (n.left, n.right):
                    ce = nid(child)
                    edges.append((me, ce))
                    walk(child)
            elif isinstance(n, UnaryOp):
                ce = nid(n.operand)
                edges.append((me, ce))
                walk(n.operand)
            elif isinstance(n, Literal):
                return
            else:
                # Unknown node may still expose children via attributes; skip
                return

        walk(self._node)
        for a, b in edges:
            lines.append(f"  {a} -> {b};")
        lines.append("}")
        return "\n".join(lines)

    def run(self, data: Series[Any] | Dataset) -> Series[Any] | dict[tuple[str, str, str], Series[Any]]:
        """Evaluate the expression against a Series or Dataset.

        - Series: evaluates directly and returns a Series.
        - Dataset: iterates keys and returns a dict keyed by (symbol, timeframe, source).
        """
        if isinstance(data, Series):
            context: dict[str, Series[Any]] = {"close": data}
            return self.evaluate(context)
        if isinstance(data, Dataset):
            # If dataset is empty, return empty mapping
            if data.is_empty:
                return {}

            # If single series, keep compatibility and return a single Series
            if len(data.keys) == 1:
                series_context = data.to_context()
                context = {name: getattr(series_context, name) for name in series_context.available_series}
                return self.evaluate(context)

            # Use requirements to build minimal per-key contexts
            req = self.requirements()
            required_fields = sorted({f.name for f in req.fields} or {"close"})

            # Gather unique (symbol, timeframe)
            st_pairs = {(k.symbol, k.timeframe) for k in data.keys}
            results: dict[tuple[str, str, str], Series[Any]] = {}
            # Simple cache for contexts per (symbol,timeframe)
            context_cache: dict[tuple[str, str], dict[str, Series[Any]]] = {}
            for symbol, timeframe in st_pairs:
                # Build or reuse context
                key2 = (symbol, timeframe)
                if key2 not in context_cache:
                    sc = data.build_context(symbol, timeframe, required_fields)
                    context_cache[key2] = {name: getattr(sc, name) for name in sc.available_series}
                out = self.evaluate(context_cache[key2])
                results[(symbol, timeframe, 'default')] = out
            return results
        raise TypeError("Expression.run expects a Series or Dataset")

    def requirements(self) -> SignalRequirements:
        """Return requirements for this expression (fields, lookbacks, derived nodes)."""
        return compute_requirements(self._node)


def _to_node(value: Expression | ExpressionNode | Series[Any] | float | int) -> ExpressionNode:
    """Convert a value to an ExpressionNode."""
    if isinstance(value, Expression):
        return value._node  # type: ignore[misc]
    elif isinstance(value, ExpressionNode):
        return value
    else:
        return Literal(value)


def as_expression(series: Series[Any]) -> Expression:
    """Convert a Series to an Expression for operator overloading."""
    return Expression(Literal(series))
