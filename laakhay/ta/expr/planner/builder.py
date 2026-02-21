"""Build canonical graphs from expression nodes."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Tuple

from ..ir.nodes import (
    CanonicalExpression, LiteralNode, CallNode, SourceRefNode,
    BinaryOpNode, UnaryOpNode, FilterNode, AggregateNode,
    TimeShiftNode, MemberAccessNode, IndexNode
)
from .types import Graph, GraphNode


def build_graph(root: CanonicalExpression) -> Graph:
    """Build a canonical graph representation for an expression node."""

    signature_cache: Dict[Tuple[Any, ...], int] = {}
    nodes: Dict[int, GraphNode] = {}
    counter = 0

    def visit(node: CanonicalExpression) -> tuple[int, Tuple[Any, ...]]:
        nonlocal counter

        if isinstance(node, BinaryOpNode):
            left_id, left_sig = visit(node.left)
            right_id, right_sig = visit(node.right)
            signature = ("BinaryOpNode", node.operator, left_sig, right_sig)
            children = (left_id, right_id)
        elif isinstance(node, UnaryOpNode):
            operand_id, operand_sig = visit(node.operand)
            signature = ("UnaryOpNode", node.operator, operand_sig)
            children = (operand_id,)
        elif isinstance(node, FilterNode):
            series_id, series_sig = visit(node.series)
            condition_id, condition_sig = visit(node.condition)
            signature = ("FilterNode", series_sig, condition_sig)
            children = (series_id, condition_id)
        elif isinstance(node, AggregateNode):
            series_id, series_sig = visit(node.series)
            signature = ("AggregateNode", node.operation, node.field, series_sig)
            children = (series_id,)
        elif isinstance(node, TimeShiftNode):
            series_id, series_sig = visit(node.series)
            signature = ("TimeShiftNode", node.shift, node.operation, series_sig)
            children = (series_id,)
        elif isinstance(node, SourceRefNode):
            signature = ("SourceRefNode", node.symbol, node.field, node.exchange, node.timeframe, node.source)
            children = ()
        elif isinstance(node, LiteralNode):
            if isinstance(node.value, list):
                literal_repr = tuple(node.value)
            elif isinstance(node.value, dict):
                literal_repr = tuple(node.value.items())
            else:
                literal_repr = node.value
            signature = ("LiteralNode", literal_repr)
            children = ()
        elif isinstance(node, CallNode):
            params_sig_items = []
            param_children_ids = []

            for key, value in sorted(node.kwargs.items()):
                child_id, child_sig = visit(value)
                params_sig_items.append((key, child_sig))
                param_children_ids.append(child_id)

            params_sig = tuple(params_sig_items)

            arg_children_ids = []
            arg_sig_items = []
            for arg in node.args:
                child_id, child_sig = visit(arg)
                arg_sig_items.append(child_sig)
                arg_children_ids.append(child_id)
                
            arg_sig = tuple(arg_sig_items)
            
            signature = ("CallNode", node.name, arg_sig, params_sig)
            children = tuple(arg_children_ids + param_children_ids)
            
        elif isinstance(node, MemberAccessNode):
            expr_id, expr_sig = visit(node.expr)
            signature = ("MemberAccessNode", expr_sig, node.member)
            children = (expr_id,)
            
        elif isinstance(node, IndexNode):
            expr_id, expr_sig = visit(node.expr)
            index_id, index_sig = visit(node.index)
            signature = ("IndexNode", expr_sig, index_sig)
            children = (expr_id, index_id)
            
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
