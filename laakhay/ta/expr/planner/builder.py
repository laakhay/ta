"""Build canonical graphs from expression nodes."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Tuple

from ..algebra.models import (
    AggregateExpression,
    BinaryOp,
    ExpressionNode,
    FilterExpression,
    Literal,
    SourceExpression,
    TimeShiftExpression,
    UnaryOp,
)
from .types import Graph, GraphNode


def _is_indicator_node(node: ExpressionNode) -> bool:
    return node.__class__.__name__ == "IndicatorNode" and hasattr(node, "name") and hasattr(node, "params")


def build_graph(root: ExpressionNode) -> Graph:
    """Build a canonical graph representation for an expression node."""

    signature_cache: Dict[Tuple[Any, ...], int] = {}
    nodes: Dict[int, GraphNode] = {}
    counter = 0

    def _hash_value(value: Any) -> str:
        if isinstance(value, int | float | str):
            rep = str(value)
        else:
            rep = repr(value)
        return hashlib.sha1(rep.encode("utf-8")).hexdigest()

    def visit(node: ExpressionNode) -> tuple[int, Tuple[Any, ...]]:
        nonlocal counter

        if isinstance(node, BinaryOp):
            left_id, left_sig = visit(node.left)
            right_id, right_sig = visit(node.right)
            signature = ("BinaryOp", node.operator.value, left_sig, right_sig)
            children = (left_id, right_id)
        elif isinstance(node, UnaryOp):
            operand_id, operand_sig = visit(node.operand)
            signature = ("UnaryOp", node.operator.value, operand_sig)
            children = (operand_id,)
        elif isinstance(node, FilterExpression):
            series_id, series_sig = visit(node.series)
            condition_id, condition_sig = visit(node.condition)
            signature = ("FilterExpression", series_sig, condition_sig)
            children = (series_id, condition_id)
        elif isinstance(node, AggregateExpression):
            series_id, series_sig = visit(node.series)
            signature = ("AggregateExpression", node.operation, node.field, series_sig)
            children = (series_id,)
        elif isinstance(node, TimeShiftExpression):
            series_id, series_sig = visit(node.series)
            signature = ("TimeShiftExpression", node.shift, node.operation, series_sig)
            children = (series_id,)
        elif isinstance(node, SourceExpression):
            signature = ("SourceExpression", node.symbol, node.field, node.exchange, node.timeframe, node.source)
            children = ()
        elif isinstance(node, Literal):
            if isinstance(node.value, list):
                literal_repr = tuple(node.value)
            else:
                literal_repr = node.value
            signature = ("Literal", literal_repr)
            children = ()
        elif _is_indicator_node(node):
            params_sig = tuple(sorted(node.params.items()))
            # If input_series is present, treat it as a child dependency
            if hasattr(node, "input_series") and node.input_series is not None:
                input_id, input_sig = visit(node.input_series)
                signature = ("Indicator", node.name, params_sig, input_sig)
                children = (input_id,)
            else:
                signature = ("Indicator", node.name, params_sig)
                children = ()
        else:
            # Fallback for unknown node types: use object id to keep determinism per instance
            signature = (type(node).__name__, id(node))
            children = ()

        if signature in signature_cache:
            node_id = signature_cache[signature]
            return node_id, signature

        node_id = counter
        counter += 1
        signature_cache[signature] = node_id

        # Compute hash from signature for structural caching
        sig_hash = hashlib.sha1(repr(signature).encode("utf-8")).hexdigest()
        nodes[node_id] = GraphNode(id=node_id, node=node, children=children, signature=signature, hash=sig_hash)
        return node_id, signature

    root_id, root_sig = visit(root)
    graph_hash = hashlib.sha1(repr(root_sig).encode("utf-8")).hexdigest()
    return Graph(root_id=root_id, nodes=nodes, hash=graph_hash)
