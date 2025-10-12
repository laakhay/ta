from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .io import TAInput, TAOutput
from .registry import INDICATORS


def stable_params_hash(params: dict[str, Any]) -> str:
    """
    Canonical, short hash for parameter dicts to key cached outputs.
    """
    payload = json.dumps(params or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class ComputeRequest(BaseModel):
    """
    Target indicator evaluation request for a single timeframe (multi-asset).
    """
    indicator_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    symbols: list[str]
    eval_ts: datetime | None = None


class PlanNode(BaseModel):
    """
    A node in the execution DAG.
    kind == "raw": key describes raw slice node (e.g., ("price","close","BTCUSDT"))
    kind == "indicator": key describes computed outputs (e.g., ("rsi","<hash>","BTCUSDT"))
    """
    kind: Literal["raw", "indicator"]
    key: tuple[str, ...]
    # Optional for indicator nodes; raw nodes generally won't need it here.
    params: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    nodes: list[PlanNode]  # topologically sorted (deps come first)


def build_execution_plan(req: ComputeRequest) -> ExecutionPlan:
    """
    Resolve dependencies from INDICATORS[req.indicator_name].requires into a DAG
    for the requested symbols (single timeframe). Topologically sort nodes.

    TODO:
      - Expand raw deps for each symbol.
      - Expand indicator deps recursively with param hashing.
      - Detect cycles and raise a clear error.
    """
    # This is an intentionally lean stub; implement in later commits.
    return ExecutionPlan(nodes=[])


def fetch_raw_slices(nodes: list[PlanNode]) -> dict[tuple[str, ...], Any]:
    """
    Fetch minimal raw series for all 'raw' nodes from data adapters.
    Apply WindowSpec at the adapter level to clip history.

    Returns:
      cache mapping: node.key -> series payload (engine-defined shape).
    """
    # Stub: wire to your data source in a later commit.
    return {}


def execute_plan(plan: ExecutionPlan, raw_cache: dict[tuple[str, ...], Any]) -> TAOutput:
    """
    Assemble TAInput per 'indicator' node, call indicator.compute, and store results
    in an in-memory cache keyed by ("name","params_hash","symbol").

    Finally, return the TAOutput for the target node.
    """
    # Stub: implement orchestration later.
    raise NotImplementedError("execute_plan is not implemented yet")
