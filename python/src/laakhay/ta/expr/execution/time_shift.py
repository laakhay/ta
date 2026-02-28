"""Shared time-shift parsing helpers."""

from __future__ import annotations


def parse_shift_periods(shift: str) -> int:
    """Parse shift string to number of periods.

    Supported formats:
    - "<n>_ago"
    - "<n>h", "<n>m"
    - "<n>"
    """
    if shift.endswith("_ago"):
        shift_part = shift[:-4]
        if shift_part.endswith("h"):
            return int(shift_part[:-1])
        if shift_part.endswith("m"):
            return int(shift_part[:-1]) // 60
        return int(shift_part)

    if shift.endswith("h"):
        return int(shift[:-1])
    if shift.endswith("m"):
        return int(shift[:-1]) // 60
    return int(shift)
