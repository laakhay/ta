"""Requirements planner for expressions/signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from ..core import Series
from .models import BinaryOp, ExpressionNode, Literal, UnaryOp
def _is_indicator_node(n: ExpressionNode) -> bool:
    return n.__class__.__name__ == "IndicatorNode" and hasattr(n, "name") and hasattr(n, "params")


@dataclass(frozen=True)
class FieldRequirement:
    name: str
    timeframe: str | None
    min_lookback: int


@dataclass(frozen=True)
class DerivedNodeReq:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    min_lookback: int = 0


@dataclass(frozen=True)
class SignalRequirements:
    fields: Tuple[FieldRequirement, ...]
    derived: Tuple[DerivedNodeReq, ...]


def _merge_field(reqs: Dict[Tuple[str, str | None], int], name: str, timeframe: str | None, lookback: int) -> None:
    key = (name, timeframe)
    prev = reqs.get(key, 0)
    if lookback > prev:
        reqs[key] = lookback


def _indicator_requirements(name: str, params: Dict[str, Any]) -> Tuple[Dict[str, int], List[DerivedNodeReq]]:
    """Return base field lookbacks and derived nodes for a given indicator name."""
    base: Dict[str, int] = {}
    derived: List[DerivedNodeReq] = []

    n = name.lower()
    period = int(params.get("period", params.get("window", 0)) or 0)

    if n in {"rolling_mean", "rolling_sum", "rolling_std", "max", "min", "sma", "ema", "rolling_ema"}:
        lb = max(1, period)
        base["close"] = lb
    elif n == "diff":
        base["close"] = 2
    elif n == "shift":
        base["close"] = max(1, abs(int(params.get("periods", 1))))
    elif n == "typical_price":
        base["high"] = 1; base["low"] = 1; base["close"] = 1
    elif n == "true_range":
        base["high"] = 1; base["low"] = 1; base["close"] = 2  # needs prev close
    elif n == "downsample":
        derived.append(DerivedNodeReq(name=n, params=params, min_lookback=max(1, int(params.get("factor", 1)))))
        base["close"] = 1
    elif n == "upsample":
        derived.append(DerivedNodeReq(name=n, params=params))
        base["close"] = 1
    elif n == "sync_timeframe":
        derived.append(DerivedNodeReq(name=n, params={k: v for k, v in params.items() if k != "reference"}))
        base["close"] = 1
    else:
        # Unknown indicator: assume close with lookback 1
        base["close"] = 1

    return base, derived


def compute_requirements(node: ExpressionNode) -> SignalRequirements:
    fields_req: Dict[Tuple[str, str | None], int] = {}
    derived_nodes: List[DerivedNodeReq] = []

    def visit(n: ExpressionNode) -> None:
        # Indicator nodes (public_api.IndicatorNode)
        if _is_indicator_node(n):
            base_map, derived = _indicator_requirements(getattr(n, "name"), getattr(n, "params"))
            for field_name, lb in base_map.items():
                # No timeframe attached here; engine can fill from dataset
                _merge_field(fields_req, field_name, None, lb)
            derived_nodes.extend(derived)
            return
        # Literals: if Series literal, record its source as field with no lookback
        if isinstance(n, Literal):
            if isinstance(n.value, Series):
                _merge_field(fields_req, "close", n.value.timeframe, 1)
            return
        # Unary op
        if isinstance(n, UnaryOp):
            visit(n.operand)
            return
        # Binary op
        if isinstance(n, BinaryOp):
            visit(n.left)
            visit(n.right)
            return

    visit(node)

    fields = tuple(FieldRequirement(name=k[0], timeframe=k[1], min_lookback=v) for k, v in fields_req.items())
    return SignalRequirements(fields=fields, derived=tuple(derived_nodes))


