"""Money Flow Index (MFI) kernel implementation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from ..kernel import Kernel


@dataclass(frozen=True)
class MFIState:
    period: int
    prev_tp: Optional[Decimal]
    pos_mf_window: tuple[Decimal, ...]
    neg_mf_window: tuple[Decimal, ...]


class MFIKernel(Kernel[MFIState]):
    def initialize(self, history: list[Any], **params: Any) -> MFIState:
        period = int(params.get("period", 14))

        if not history:
            return MFIState(period=period, prev_tp=None, pos_mf_window=(), neg_mf_window=())

        # Initialization logic:
        # We need typical price and previous typical price
        # HLC3 = (H+L+C)/3
        # Money Flow = HLC3 * Volume

        prev_tp: Optional[Decimal] = None
        pos_mfs = []
        neg_mfs = []

        for h, l, c, v in history:
            h, l, c, v = [Decimal(str(x)) for x in (h, l, c, v)]
            tp = (h + l + c) / Decimal(3)

            if prev_tp is not None:
                mf = tp * v
                if tp > prev_tp:
                    pos_mfs.append(mf)
                    neg_mfs.append(Decimal(0))
                elif tp < prev_tp:
                    pos_mfs.append(Decimal(0))
                    neg_mfs.append(mf)
                else:
                    pos_mfs.append(Decimal(0))
                    neg_mfs.append(Decimal(0))

            prev_tp = tp

            if len(pos_mfs) > period:
                pos_mfs.pop(0)
                neg_mfs.pop(0)

        return MFIState(period=period, prev_tp=prev_tp, pos_mf_window=tuple(pos_mfs), neg_mf_window=tuple(neg_mfs))

    def step(self, state: MFIState, x_t: Any, **params: Any) -> tuple[MFIState, Decimal]:
        h, l, c, v = [Decimal(str(x)) for x in x_t]
        tp = (h + l + c) / Decimal(3)

        pos_win = list(state.pos_mf_window)
        neg_win = list(state.neg_mf_window)

        if state.prev_tp is None:
            # First bar cannot have a flow
            return MFIState(
                period=state.period, prev_tp=tp, pos_mf_window=tuple(pos_win), neg_mf_window=tuple(neg_win)
            ), Decimal(0)

        mf = tp * v
        if tp > state.prev_tp:
            pos_win.append(mf)
            neg_win.append(Decimal(0))
        elif tp < state.prev_tp:
            pos_win.append(Decimal(0))
            neg_win.append(mf)
        else:
            pos_win.append(Decimal(0))
            neg_win.append(Decimal(0))

        if len(pos_win) > state.period:
            pos_win.pop(0)
            neg_win.pop(0)

        mfi = Decimal(0)
        if len(pos_win) == state.period:
            sum_pos = sum(pos_win)
            sum_neg = sum(neg_win)

            if sum_neg == 0:
                mfi = Decimal(100)
            else:
                money_ratio = sum_pos / sum_neg
                mfi = Decimal(100) - (Decimal(100) / (Decimal(1) + money_ratio))

        return MFIState(
            period=state.period, prev_tp=tp, pos_mf_window=tuple(pos_win), neg_mf_window=tuple(neg_win)
        ), mfi
