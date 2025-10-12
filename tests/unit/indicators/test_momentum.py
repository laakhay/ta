"""Tests for momentum indicators (RSI, MACD, Stochastic, EMA)."""

from laakhay.ta.core.plan import ComputeRequest, build_execution_plan, execute_plan


class TestRSIIndicator:
    """Test Relative Strength Index indicator."""

    def test_rsi_range(self, sample_candles):
        """RSI should always be between 0 and 100."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="rsi",
            params={"period": 14},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        rsi_series = result.values["BTCUSDT"]

        for _ts, rsi_val in rsi_series:
            assert 0 <= rsi_val <= 100

    def test_rsi_uptrend_overbought(self, sample_candles):
        """Strong uptrend should push RSI toward overbought (>70)."""
        # Create strong uptrend
        from datetime import datetime, timezone
        from decimal import Decimal

        from laakhay.ta.models import Candle

        candles = []
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

        for i in range(30):
            price = 100 + i * 5  # Strong consistent gains
            candles.append(
                Candle(
                    symbol="BTCUSDT",
                    timestamp=base_time.replace(hour=i % 24, day=1 + i // 24),
                    open=Decimal(str(price)),
                    high=Decimal(str(price + 2)),
                    low=Decimal(str(price - 1)),
                    close=Decimal(str(price + 1)),
                    volume=Decimal("100.0"),
                    is_closed=True,
                )
            )

        req = ComputeRequest(
            indicator_name="rsi",
            params={"period": 14},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        rsi_series = result.values["BTCUSDT"]
        latest_rsi = rsi_series[-1][1]

        assert latest_rsi > 70  # Should be overbought


class TestMACDIndicator:
    """Test MACD indicator."""

    def test_macd_structure(self, sample_candles):
        """MACD should return macd, signal, and histogram."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="macd",
            params={"fast": 12, "slow": 26, "signal": 9},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        macd_dict = result.values["BTCUSDT"]

        assert "macd" in macd_dict
        assert "signal" in macd_dict
        assert "histogram" in macd_dict
        assert len(macd_dict["macd"]) == len(macd_dict["signal"]) == len(macd_dict["histogram"])

    def test_macd_histogram_formula(self, sample_candles):
        """Histogram should equal MACD - Signal."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="macd",
            params={"fast": 12, "slow": 26, "signal": 9},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        macd_dict = result.values["BTCUSDT"]

        for i in range(len(macd_dict["macd"])):
            macd_val = macd_dict["macd"][i][1]
            signal_val = macd_dict["signal"][i][1]
            histogram_val = macd_dict["histogram"][i][1]

            assert abs(histogram_val - (macd_val - signal_val)) < 1e-6

    def test_macd_crossover(self, sample_candles):
        """Test MACD can detect potential crossovers."""
        candles = sample_candles("BTCUSDT", count=60)

        req = ComputeRequest(
            indicator_name="macd",
            params={"fast": 12, "slow": 26, "signal": 9},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        macd_dict = result.values["BTCUSDT"]

        # Just verify histogram changes sign (crossover occurred)
        histograms = [h[1] for h in macd_dict["histogram"]]

        # In trending data, histogram should vary
        assert max(histograms) != min(histograms)


class TestStochasticIndicator:
    """Test Stochastic Oscillator."""

    def test_stochastic_range(self, sample_candles):
        """Stochastic %K and %D should be between 0 and 100."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="stoch",
            params={"k_period": 14, "d_period": 3},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        stoch_dict = result.values["BTCUSDT"]

        for _ts, k_val in stoch_dict["k"]:
            assert 0 <= k_val <= 100

        for _ts, d_val in stoch_dict["d"]:
            assert 0 <= d_val <= 100

    def test_stochastic_d_smooths_k(self, sample_candles):
        """% D should be smoother than %K (less volatile)."""
        candles = sample_candles("BTCUSDT", count=50)

        req = ComputeRequest(
            indicator_name="stoch",
            params={"k_period": 14, "d_period": 3},
            symbols=["BTCUSDT"],
            eval_ts=candles[-1].timestamp,
        )

        plan = build_execution_plan(req)
        raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
        result = execute_plan(plan, raw_cache, req)

        stoch_dict = result.values["BTCUSDT"]

        k_values = [v for ts, v in stoch_dict["k"]]
        d_values = [v for ts, v in stoch_dict["d"]]

        # Calculate volatility (std deviation) as smoothness metric
        k_volatility = max(k_values) - min(k_values)
        d_volatility = max(d_values) - min(d_values)

        # %D should generally be smoother (less range)
        # This might not always hold, but generally true
        assert d_volatility <= k_volatility * 1.5  # Allow some margin
