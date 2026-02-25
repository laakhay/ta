"""ADX Kernel implementation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..kernel import Kernel


@dataclass
class ADXState:
    """State for ADX."""

    period: int
    prev_high: Decimal | None
    prev_low: Decimal | None
    prev_close: Decimal | None
    smoothed_tr: Decimal | None
    smoothed_plus_dm: Decimal | None
    smoothed_minus_dm: Decimal | None
    smoothed_dx: Decimal | None


class ADXKernel(Kernel[ADXState]):
    """Kernel for evaluating Average Directional Index (ADX)."""

    def initialize(self, history: list[Any], **params: Any) -> ADXState:
        period = int(params.get("period", 14))

        if not history:
            return ADXState(
                period=period,
                prev_high=None,
                prev_low=None,
                prev_close=None,
                smoothed_tr=None,
                smoothed_plus_dm=None,
                smoothed_minus_dm=None,
                smoothed_dx=None,
            )

        # ADX initialization is complex. Standard RMA start:
        # 1. Calculate TR, +DM, -DM for all history
        # 2. Smooth them using RMA logic

        prev_h: Decimal | None = None
        prev_l: Decimal | None = None
        prev_c: Decimal | None = None

        s_tr: Decimal | None = None
        s_pdm: Decimal | None = None
        s_mdm: Decimal | None = None
        s_dx: Decimal | None = None

        alpha = Decimal(1) / Decimal(period)

        for x_t in history:
            h, l, c = x_t

            # TR
            if prev_c is None:
                tr = h - l
            else:
                tr = max(h - l, abs(h - prev_c), abs(l - prev_c))

            # DM
            pdm = Decimal(0)
            mdm = Decimal(0)
            if prev_h is not None and prev_l is not None:
                up = h - prev_h
                down = prev_l - l
                if up > down and up > 0:
                    pdm = up
                if down > up and down > 0:
                    mdm = down

            # Smoothing (RMA)
            if s_tr is None:
                s_tr = tr
                s_pdm = pdm
                s_mdm = mdm
            else:
                s_tr = alpha * tr + (Decimal(1) - alpha) * s_tr
                s_pdm = alpha * pdm + (Decimal(1) - alpha) * s_pdm
                s_mdm = alpha * mdm + (Decimal(1) - alpha) * s_mdm

            # DX
            if s_tr and s_tr > 0:
                pdi = Decimal(100) * (s_pdm / s_tr)
                mdi = Decimal(100) * (s_mdm / s_tr)
                denom = pdi + mdi
                dx = Decimal(100) * abs(pdi - mdi) / denom if denom > 0 else Decimal(0)

                if s_dx is None:
                    s_dx = dx
                else:
                    s_dx = alpha * dx + (Decimal(1) - alpha) * s_dx

            prev_h, prev_l, prev_c = h, l, c

        return ADXState(
            period=period,
            prev_high=prev_h,
            prev_low=prev_l,
            prev_close=prev_c,
            smoothed_tr=s_tr,
            smoothed_plus_dm=s_pdm,
            smoothed_minus_dm=s_mdm,
            smoothed_dx=s_dx,
        )

    def step(self, state: ADXState, x_t: Any, **params: Any) -> tuple[ADXState, tuple[Decimal, Decimal, Decimal]]:
        h, l, c = x_t

        # TR
        if state.prev_close is None:
            tr = h - l
        else:
            tr = max(h - l, abs(h - state.prev_close), abs(l - state.prev_close))

        # DM
        pdm = Decimal(0)
        mdm = Decimal(0)
        if state.prev_high is not None and state.prev_low is not None:
            up = h - state.prev_high
            down = state.prev_low - l
            if up > down and up > 0:
                pdm = up
            if down > up and down > 0:
                mdm = down

        alpha = Decimal(1) / Decimal(state.period)

        # Smoothing
        if state.smoothed_tr is None:
            new_s_tr = tr
            new_s_pdm = pdm
            new_s_mdm = mdm
        else:
            new_s_tr = alpha * tr + (Decimal(1) - alpha) * state.smoothed_tr
            new_s_pdm = alpha * pdm + (Decimal(1) - alpha) * state.smoothed_plus_dm
            new_s_mdm = alpha * mdm + (Decimal(1) - alpha) * state.smoothed_minus_dm

        pdi = Decimal(0)
        mdi = Decimal(0)
        dx = Decimal(0)

        if new_s_tr > 0:
            pdi = Decimal(100) * (new_s_pdm / new_s_tr)
            mdi = Decimal(100) * (new_s_mdm / new_s_tr)
            denom = pdi + mdi
            dx = Decimal(100) * abs(pdi - mdi) / denom if denom > 0 else Decimal(0)

        if state.smoothed_dx is None:
            new_s_dx = dx
        else:
            new_s_dx = alpha * dx + (Decimal(1) - alpha) * state.smoothed_dx

        new_state = ADXState(
            period=state.period,
            prev_high=h,
            prev_low=l,
            prev_close=c,
            smoothed_tr=new_s_tr,
            smoothed_plus_dm=new_s_pdm,
            smoothed_minus_dm=new_s_mdm,
            smoothed_dx=new_s_dx,
        )

        return new_state, (new_s_dx, pdi, mdi)
