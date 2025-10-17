"""Tests for volume indicators (VWAP, Volume SMA, Volume ROC)."""

from laakhay.ta.core.plan import ComputeRequest, build_execution_plan, execute_plan


class TestVWAPIndicator:
    """Test Volume Weighted Average Price indicator."""

    def test_vwap_price_range(self, sample_candles):
        """VWAP should be within the price range of the candles."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="vwap",
            params={},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        vwap_series = result.values["BTCUSDT"]

        # Find price bounds
        all_highs = [float(c.high) for c in candles]
        all_lows = [float(c.low) for c in candles]
        max_price = max(all_highs)
        min_price = min(all_lows)

        for _ts, vwap_val in vwap_series:
            assert min_price <= vwap_val <= max_price

    def test_vwap_volume_weighting(self, sample_candles):
        """VWAP should weight prices by volume."""
        from datetime import datetime, timezone
        from decimal import Decimal

        from laakhay.ta.models import Candle

        # Create candles with specific volume patterns
        candles = []
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

        # First 10: high volume at low price
        for i in range(10):
            candles.append(
                Candle(
                    symbol="BTCUSDT",
                    timestamp=base_time.replace(hour=i),
                    open=Decimal("100.0"),
                    high=Decimal("101.0"),
                    low=Decimal("99.0"),
                    close=Decimal("100.0"),
                    volume=Decimal("1000.0"),  # High volume
                    is_closed=True,
                )
            )

        # Next 10: low volume at high price
        for i in range(10, 20):
            candles.append(
                Candle(
                    symbol="BTCUSDT",
                    timestamp=base_time.replace(hour=i),
                    open=Decimal("200.0"),
                    high=Decimal("201.0"),
                    low=Decimal("199.0"),
                    close=Decimal("200.0"),
                    volume=Decimal("10.0"),  # Low volume
                    is_closed=True,
                )
            )

        req = ComputeRequest(
            indicator_name="vwap",
            params={},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        vwap_series = result.values["BTCUSDT"]
        final_vwap = vwap_series[-1][1]

        # VWAP should be closer to 100 (high volume) than 200 (low volume)
        assert final_vwap < 150

    def test_vwap_cumulative(self, sample_candles):
        """VWAP should be cumulative (each point considers all prior data)."""
        candles = sample_candles("BTCUSDT", count=30)

        req = ComputeRequest(
            indicator_name="vwap",
            params={},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        vwap_series = result.values["BTCUSDT"]

        # VWAP series length should equal input candles (cumulative from start)
        assert len(vwap_series) == len(candles)

    def test_vwap_typical_price(self, sample_candles):
        """VWAP should use typical price (H+L+C)/3."""
        from datetime import datetime, timezone
        from decimal import Decimal

        from laakhay.ta.models import Candle

        # Single candle with known values
        candle = Candle(
            symbol="BTCUSDT",
            timestamp=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            open=Decimal("100.0"),
            high=Decimal("105.0"),
            low=Decimal("95.0"),
            close=Decimal("100.0"),
            volume=Decimal("100.0"),
            is_closed=True,
        )

        req = ComputeRequest(
            indicator_name="vwap",
            params={},
            symbols=["BTCUSDT"],
            eval_ts=candle.timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): [candle]}
        result = execute_plan(plan, raw_cache, req)

        vwap_val = result.values["BTCUSDT"][0][1]

        # Typical price = (105 + 95 + 100) / 3 = 100
        expected = (105.0 + 95.0 + 100.0) / 3
        assert abs(vwap_val - expected) < 0.01


class TestSimpleVolumeAverageIndicator:
    """Test Simple Volume Average (Volume SMA) indicator."""

    def test_volume_sma_basic(self, sample_candles):
        """Volume SMA should match arithmetic mean of the window."""
        from decimal import Decimal

        candles = sample_candles("BTCUSDT", count=5)
        custom_volumes = [100, 200, 300, 400, 500]
        candles = [
            candle.model_copy(update={"volume": Decimal(str(volume))})
            for candle, volume in zip(candles, custom_volumes, strict=True)
        ]

        req = ComputeRequest(
            indicator_name="volume_sma",
            params={"period": 3},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        sma_series = result.values["BTCUSDT"]

        assert len(sma_series) == 3  # 5 - 3 + 1

        expected_values = [
            (100 + 200 + 300) / 3,
            (200 + 300 + 400) / 3,
            (300 + 400 + 500) / 3,
        ]

        for (_ts, value), expected in zip(sma_series, expected_values, strict=True):
            assert abs(value - expected) < 1e-6


class TestVolumeROCIndicator:
    """Test Volume Rate of Change indicator."""

    def test_volume_roc_percentage(self, sample_candles):
        """Volume ROC should compute percentage change vs period bars ago."""
        from decimal import Decimal

        candles = sample_candles("BTCUSDT", count=5)
        custom_volumes = [100, 200, 400, 200, 100]
        candles = [
            candle.model_copy(update={"volume": Decimal(str(volume))})
            for candle, volume in zip(candles, custom_volumes, strict=True)
        ]

        req = ComputeRequest(
            indicator_name="volume_roc",
            params={"period": 2, "multiplier": 100.0},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        roc_series = result.values["BTCUSDT"]

        assert len(roc_series) == 3  # 5 - 2

        expected_values = [300.0, 0.0, -75.0]
        for (_ts, value), expected in zip(roc_series, expected_values, strict=True):
            assert abs(value - expected) < 1e-6

    def test_volume_roc_zero_previous_volume(self, sample_candles):
        """When prior volume is zero, ROC should return zero to avoid division by zero."""
        from decimal import Decimal

        candles = sample_candles("BTCUSDT", count=3)
        custom_volumes = [0, 150, 300]
        candles = [
            candle.model_copy(update={"volume": Decimal(str(volume))})
            for candle, volume in zip(candles, custom_volumes, strict=True)
        ]

        req = ComputeRequest(
            indicator_name="volume_roc",
            params={"period": 2},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        roc_series = result.values["BTCUSDT"]
        assert len(roc_series) == 1
        assert roc_series[0][1] == 0.0
