import pytest

from laakhay.ta.expr.ir.nodes import BinaryOpNode, LiteralNode, UnaryOpNode
from laakhay.ta.expr.planner.evaluator import Evaluator
from laakhay.ta.expr.planner.types import (
    AlignmentPolicy,
    Graph,
    GraphNode,
    PlanResult,
    SignalRequirements,
)


# Minimal mocks and helpers
def make_simple_plan(node):
    return PlanResult(
        graph=Graph(
            root_id=0,
            nodes={0: GraphNode(0, node, (), (), "test-hash")},
            hash="test-hash",
        ),
        node_order=(0,),
        requirements=SignalRequirements(),
        alignment=AlignmentPolicy(),
    )


def test_literal_node():
    evaluator = Evaluator()
    node = LiteralNode(42)
    plan = make_simple_plan(node)
    result = evaluator._evaluate_graph(plan, context={})
    assert result == 42


def test_binaryop_node():
    evaluator = Evaluator()
    # 5 + 3
    left = LiteralNode(5)
    right = LiteralNode(3)
    node = BinaryOpNode("add", left, right)  # Use string operator for Canonical IR
    # Simulate plan with binaryop as root, children as nodes 1 (left) and 2 (right)
    nodes = {
        0: GraphNode(0, node, (1, 2), (), "binop"),
        1: GraphNode(1, left, (), (), "binop"),
        2: GraphNode(2, right, (), (), "binop"),
    }
    plan = PlanResult(
        graph=Graph(root_id=0, nodes=nodes, hash="binop"),
        node_order=(1, 2, 0),
        requirements=SignalRequirements(),
        alignment=AlignmentPolicy(),
    )
    result = evaluator._evaluate_graph(plan, context={})
    assert getattr(result, "values", (result,))[0] == 8


def test_unaryop_node():
    evaluator = Evaluator()
    # -7
    operand = LiteralNode(7)
    node = UnaryOpNode("neg", operand)
    nodes = {
        0: GraphNode(0, node, (1,), (), "uop"),
        1: GraphNode(1, operand, (), (), "uop"),
    }
    plan = PlanResult(
        graph=Graph(root_id=0, nodes=nodes, hash="uop"),
        node_order=(1, 0),
        requirements=SignalRequirements(),
        alignment=AlignmentPolicy(),
    )
    result = evaluator._evaluate_graph(plan, context={})
    assert getattr(result, "values", (result,))[0] == -7


def test_shared_subgraph_cache():
    evaluator = Evaluator()
    # Build a graph of: sub = (4 + 2); root = sub + sub
    l1 = LiteralNode(4)
    l2 = LiteralNode(2)
    sub = BinaryOpNode("add", l1, l2)
    root = BinaryOpNode("add", sub, sub)
    nodes = {
        0: GraphNode(0, root, (1, 1), (), "shared-cache"),
        1: GraphNode(1, sub, (2, 3), (), "shared-cache"),
        2: GraphNode(2, l1, (), (), "shared-cache"),
        3: GraphNode(3, l2, (), (), "shared-cache"),
    }
    plan = PlanResult(
        graph=Graph(root_id=0, nodes=nodes, hash="shared-cache"),
        node_order=(2, 3, 1, 0),
        requirements=SignalRequirements(),
        alignment=AlignmentPolicy(),
    )
    result = evaluator._evaluate_graph(plan, context={})
    assert getattr(result, "values", (result,))[0] == 12  # (4+2)+(4+2)
    # The subgraph (node 1) is used twice; caching ensures its computation is reused.


# Run pytest if this script is run standalone
if __name__ == "__main__":
    pytest.main([__file__])
