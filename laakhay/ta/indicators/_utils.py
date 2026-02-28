import math
from typing import Any
from ..core import Series as CoreSeries
from ..core.types import Price

def results_to_series(
    results: list[float], 
    ctx_series: CoreSeries[Any], 
    value_class: type = Price
) -> CoreSeries[Any]:
    """Converts a list of floats (with optional NaNs) from Rust to a CoreSeries."""
    mask = tuple(not math.isnan(v) for v in results)
    values = tuple(value_class("NaN") if math.isnan(v) else value_class(str(v)) for v in results)
    
    return CoreSeries[Any](
        timestamps=ctx_series.timestamps,
        values=values,
        symbol=ctx_series.symbol,
        timeframe=ctx_series.timeframe,
        availability_mask=mask,
    )
