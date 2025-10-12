"""
Statistical Utilities Module

Provides stateless statistical analysis tools for market data.
Implements returns calculation, percentile ranking, z-score calculation,
and other statistical utilities commonly used in technical analysis.

Design:
- Stateless: Pure functions with @staticmethod
- Type-safe: Proper type hints for all functions
- Deterministic: Same inputs always produce same outputs
- Flexible: Multiple methods for returns and statistics
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from math import log
from statistics import mean, stdev
from typing import Literal


class StatisticalUtils:
    """Stateless statistical utilities for technical analysis.

    Provides methods for:
    - Returns calculation (log, percentage, simple)
    - Percentile ranking
    - Z-score calculation
    - Statistical analysis

    Example:
        >>> prices = [Decimal("100"), Decimal("105"), Decimal("103")]
        >>> log_returns = StatisticalUtils.calculate_returns(prices, method="log")
        >>> pct_returns = StatisticalUtils.calculate_returns(prices, method="pct")
        >>>
        >>> value = 105.0
        >>> values = [100.0, 101.0, 102.0, 103.0, 104.0]
        >>> percentile = StatisticalUtils.percentile_rank(value, values)
        >>> zscore = StatisticalUtils.zscore(value, values)
    """

    @staticmethod
    def calculate_returns(
        prices: Sequence[Decimal],
        method: Literal["log", "pct", "simple"] = "log",
    ) -> list[float]:
        """Calculate returns from price series.

        Args:
            prices: Sequence of prices
            method: Returns calculation method:
                - "log": Log returns (ln(p_t / p_{t-1}))
                - "pct": Percentage returns ((p_t - p_{t-1}) / p_{t-1})
                - "simple": Simple returns (p_t - p_{t-1})

        Returns:
            List of returns (length = len(prices) - 1)

        Raises:
            ValueError: If method is invalid or prices has < 2 elements

        Example:
            >>> prices = [Decimal("100"), Decimal("105"), Decimal("110")]
            >>> log_rets = StatisticalUtils.calculate_returns(prices, method="log")
            >>> pct_rets = StatisticalUtils.calculate_returns(prices, method="pct")
            >>> # log_rets ≈ [0.0488, 0.0465]
            >>> # pct_rets = [0.05, 0.0476]
        """
        if len(prices) < 2:
            raise ValueError("Need at least 2 prices to calculate returns")

        if method not in ("log", "pct", "simple"):
            raise ValueError(f"Invalid method: {method}. Must be 'log', 'pct', or 'simple'.")

        prices_float = [float(p) for p in prices]

        if method == "log":
            returns = [
                log(prices_float[i] / prices_float[i - 1])
                for i in range(1, len(prices_float))
            ]
        elif method == "pct":
            returns = [
                (prices_float[i] - prices_float[i - 1]) / prices_float[i - 1]
                for i in range(1, len(prices_float))
            ]
        else:  # simple
            returns = [
                prices_float[i] - prices_float[i - 1]
                for i in range(1, len(prices_float))
            ]

        return returns

    @staticmethod
    def percentile_rank(value: float, values: Sequence[float]) -> float:
        """Calculate percentile rank of a value in a distribution.

        Args:
            value: Value to rank
            values: Distribution of values to compare against

        Returns:
            Percentile rank (0-100)

        Example:
            >>> values = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
            >>> percentile = StatisticalUtils.percentile_rank(103.5, values)
            >>> # percentile ≈ 60.0 (above 60% of values)
        """
        if not values:
            return 0.0

        count_below = sum(1 for v in values if v < value)
        return (count_below / len(values)) * 100

    @staticmethod
    def zscore(value: float, values: Sequence[float]) -> float:
        """Calculate z-score of a value.

        The z-score represents how many standard deviations a value is from the mean.

        Args:
            value: Value to score
            values: Distribution of values to compare against

        Returns:
            Z-score (standard deviations from mean)

        Example:
            >>> values = [100.0, 102.0, 104.0, 106.0, 108.0]
            >>> z = StatisticalUtils.zscore(112.0, values)
            >>> # z ≈ 2.0 (2 std devs above mean)
        """
        if not values or len(values) < 2:
            return 0.0

        mean_val = mean(values)
        std_val = stdev(values)

        if std_val == 0:
            return 0.0

        return (value - mean_val) / std_val

    @staticmethod
    def calculate_volatility(
        returns: Sequence[float],
        annualization_factor: float = 1.0,
    ) -> float:
        """Calculate volatility (standard deviation of returns).

        Args:
            returns: Sequence of returns (e.g., from calculate_returns)
            annualization_factor: Factor to annualize volatility
                - For daily returns: 252 (trading days)
                - For hourly returns: 24 * 365
                - For minute returns: 60 * 24 * 365

        Returns:
            Volatility (annualized if factor > 1)

        Example:
            >>> returns = [0.01, -0.005, 0.02, -0.01, 0.015]
            >>> vol = StatisticalUtils.calculate_volatility(returns)
            >>> ann_vol = StatisticalUtils.calculate_volatility(returns, 252)
        """
        if not returns or len(returns) < 2:
            return 0.0

        std = stdev(returns)
        return std * (annualization_factor ** 0.5)

    @staticmethod
    def calculate_sharpe_ratio(
        returns: Sequence[float],
        risk_free_rate: float = 0.0,
        annualization_factor: float = 1.0,
    ) -> float:
        """Calculate Sharpe ratio (risk-adjusted returns).

        The Sharpe ratio measures excess return per unit of risk.

        Args:
            returns: Sequence of returns
            risk_free_rate: Risk-free rate (same period as returns)
            annualization_factor: Factor to annualize Sharpe ratio

        Returns:
            Sharpe ratio (higher is better)

        Example:
            >>> returns = [0.01, 0.02, -0.005, 0.015, 0.01]
            >>> sharpe = StatisticalUtils.calculate_sharpe_ratio(
            ...     returns, risk_free_rate=0.001, annualization_factor=252
            ... )
        """
        if not returns or len(returns) < 2:
            return 0.0

        mean_return = mean(returns)
        std_return = stdev(returns)

        if std_return == 0:
            return 0.0

        excess_return = mean_return - risk_free_rate
        sharpe = excess_return / std_return

        return sharpe * (annualization_factor ** 0.5)
