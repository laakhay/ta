"""Build canonical graphs from expression nodes."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Tuple

from ..expressions.models import BinaryOp, ExpressionNode, Literal, UnaryOp
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
        elif isinstance(node, Literal):
            if isinstance(node.value, list):
                literal_repr = tuple(node.value)
            else:
                literal_repr = node.value
            signature = ("Literal", literal_repr)
            children = ()
        elif _is_indicator_node(node):
            params_sig = tuple(sorted(node.params.items()))
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
