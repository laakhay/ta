from datetime import datetime, timedelta

from laakhay.ta.expr.runtime.preview import preview


def test_nested_indicator_plotting():
    # Setup some dummy data
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(100)]
    bars = [
        {"timestamp": d, "open": 100 + i, "high": 110 + i, "low": 90 + i, "close": 105 + i, "volume": 1000}
        for i, d in enumerate(dates)
    ]

    # Define a nested expression: crossup(ema(10), ema(20))
    # We expect ema_10 and ema_20 series to be present in the preview result
    expr_text = "crossup(ema(10), ema(20))"

    result = preview(expr_text, bars=bars, symbol="BTC/USDT", timeframe="1d")

    # Check if indicator series are captured
    assert result.indicator_series is not None
    print(f"Captured indicators: {list(result.indicator_series.keys())}")

    # We expect keys like "ema_..."
    # Currently, because build_graph doesn't traverse params, these might be missing
    ema_keys = [k for k in result.indicator_series.keys() if "ema" in k]
    assert len(ema_keys) >= 2, f"Expected at least 2 EMA series, found {len(ema_keys)}: {ema_keys}"
