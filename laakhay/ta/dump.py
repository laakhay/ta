"""Legacy shim to maintain `laakhay.ta.dump.to_csv` imports.

Implementation moved to `laakhay.ta.io.csv`.
"""

from __future__ import annotations

from .io.csv import to_csv  # re-export for backward compatibility

__all__ = ["to_csv"]
