"""Tests for trend indicators (SMA, EMA, Bollinger Bands)."""

from laakhay.ta.core.plan import ComputeRequest, build_execution_plan, execute_plan


class TestSMAIndicator:
    """Test Simple Moving Average indicator."""

    def test_sma_basic_calculation(self, sample_candles):
        """SMA should return correct moving average."""
        candles = sample_candles("BTCUSDT", count=30, base_price=100.0)

        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 5, "price_field": "close"},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        sma_series = result.values["BTCUSDT"]

        # Should have 30 - 5 + 1 = 26 values
        assert len(sma_series) == 26

        # First SMA should be average of first 5 closes
        # Closes are: 101, 102, 103, 104, 105
        first_sma = (101 + 102 + 103 + 104 + 105) / 5
        assert abs(sma_series[0][1] - first_sma) < 1e-6

    def test_sma_series_length(self, sample_candles):
        """SMA series length should match formula: len(candles) - period + 1."""
        candles = sample_candles("BTCUSDT", count=100)

        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 20},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        assert len(result.values["BTCUSDT"]) == 81  # 100 - 20 + 1

    def test_sma_different_price_fields(self, sample_candles):
        """SMA should work with different price fields."""
        candles = sample_candles("BTCUSDT", count=30)

        # Test with close (default)
        req = ComputeRequest(
            indicator_name="sma",
            params={"period": 10, "price_field": "close"},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        assert len(result.values["BTCUSDT"]) == 21  # 30 - 10 + 1
        assert "BTCUSDT" in result.values


class TestEMAIndicator:
    """Test Exponential Moving Average indicator."""

    def test_ema_basic_calculation(self, sample_candles):
        """EMA should apply exponential smoothing correctly."""
        candles = sample_candles("BTCUSDT", count=30, base_price=100.0)

        req = ComputeRequest(
            indicator_name="ema",
            params={"period": 5, "price_field": "close"},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        ema_series = result.values["BTCUSDT"]

        # First EMA should equal SMA of first 5 values
        first_sma = (101 + 102 + 103 + 104 + 105) / 5
        assert abs(ema_series[0][1] - first_sma) < 1e-6

        # Subsequent values should be > previous (uptrend)
        assert ema_series[-1][1] > ema_series[0][1]


class TestBollingerBandsIndicator:
    """Test Bollinger Bands indicator."""

    def test_bbands_structure(self, sample_candles):
        """Bollinger Bands should return upper, middle, lower bands."""
        candles = sample_candles("BTCUSDT", count=30)

        req = ComputeRequest(
            indicator_name="bbands",
            params={"period": 20, "num_std": 2.0},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        bb_dict = result.values["BTCUSDT"]

        assert "upper" in bb_dict
        assert "middle" in bb_dict
        assert "lower" in bb_dict
        assert len(bb_dict["upper"]) == len(bb_dict["middle"]) == len(bb_dict["lower"])

    def test_bbands_band_order(self, sample_candles):
        """Upper band > Middle band > Lower band always."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="bbands",
            params={"period": 20, "num_std": 2.0},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        bb_dict = result.values["BTCUSDT"]

        for i in range(len(bb_dict["upper"])):
            upper_val = bb_dict["upper"][i][1]
            middle_val = bb_dict["middle"][i][1]
            lower_val = bb_dict["lower"][i][1]

            assert upper_val > middle_val > lower_val

    def test_bbands_bandwidth_scales_with_std(self, sample_candles):
        """Bandwidth should scale proportionally with num_std."""
        candles = sample_candles("BTCUSDT", count=50)

        req_2std = ComputeRequest(
            indicator_name="bbands",
            params={"period": 20, "num_std": 2.0},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        req_3std = ComputeRequest(
            indicator_name="bbands",
            params={"period": 20, "num_std": 3.0},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req_2std)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}

        result_2std = execute_plan(plan, raw_cache, req_2std)
        result_3std = execute_plan(build_execution_plan(req_3std), raw_cache, req_3std)

        bb_2std = result_2std.values["BTCUSDT"]
        bb_3std = result_3std.values["BTCUSDT"]

        bw_2std = bb_2std["upper"][-1][1] - bb_2std["lower"][-1][1]
        bw_3std = bb_3std["upper"][-1][1] - bb_3std["lower"][-1][1]

        # Ratio should be ~1.5
        assert abs(bw_3std / bw_2std - 1.5) < 0.01
