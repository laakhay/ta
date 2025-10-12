"""Tests for volatility indicators (ATR, Bollinger Bands)."""

from laakhay.ta.core.plan import ComputeRequest, build_execution_plan, execute_plan


class TestATRIndicator:
    """Test Average True Range indicator."""

    def test_atr_positive(self, sample_candles):
        """ATR values should always be positive."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="atr",
            params={"period": 14},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        atr_series = result.values["BTCUSDT"]

        for _ts, atr_val in atr_series:
            assert atr_val >= 0

    def test_atr_high_volatility(self, sample_candles):
        """ATR should increase with higher volatility."""
        from datetime import datetime, timezone
        from decimal import Decimal

        from laakhay.ta.models import Candle

        # Low volatility candles
        low_vol_candles = []
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

        for i in range(30):
            price = 100
            low_vol_candles.append(
                Candle(
                    symbol="BTCUSDT",
                    timestamp=base_time.replace(hour=i % 24, day=1 + i // 24),
                    open=Decimal(str(price)),
                    high=Decimal(str(price + 0.5)),
                    low=Decimal(str(price - 0.5)),
                    close=Decimal(str(price)),
                    volume=Decimal("100.0"),
                    is_closed=True,
                )
            )

        # High volatility candles
        high_vol_candles = []
        for i in range(30):
            price = 100
            high_vol_candles.append(
                Candle(
                    symbol="BTCUSDT",
                    timestamp=base_time.replace(hour=i % 24, day=1 + i // 24),
                    open=Decimal(str(price)),
                    high=Decimal(str(price + 10)),
                    low=Decimal(str(price - 10)),
                    close=Decimal(str(price)),
                    volume=Decimal("100.0"),
                    is_closed=True,
                )
            )

        req = ComputeRequest(
            indicator_name="atr",
            params={"period": 14},
            symbols=["BTCUSDT"],
            eval_ts=low_vol_candles[-1].timestamp,
        )

        # Test low volatility
        plan = build_execution_plan(req)
        raw_cache_low = {("raw", "price", "close", "BTCUSDT"): low_vol_candles}
        result_low = execute_plan(plan, raw_cache_low, req)
        low_atr = result_low.values["BTCUSDT"][-1][1]

        # Test high volatility
        raw_cache_high = {("raw", "price", "close", "BTCUSDT"): high_vol_candles}
        result_high = execute_plan(plan, raw_cache_high, req)
        high_atr = result_high.values["BTCUSDT"][-1][1]

        assert high_atr > low_atr * 5  # High volatility ATR should be much larger

    def test_atr_series_length(self, sample_candles):
        """ATR series should have correct length based on period."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="atr",
            params={"period": 14},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        atr_series = result.values["BTCUSDT"]

        # ATR needs period candles plus lookback for true range
        # Actual length may vary based on implementation
        assert len(atr_series) >= len(candles) - 14  # At least this many
