"""Relative Strength Index (RSI) indicator using primitives."""

from __future__ import annotations

from .. import register, SeriesContext, Price, Expression, Literal, diff, negative_values, positive_values, rolling_mean


@register("rsi", description="Relative Strength Index")
def rsi(ctx: SeriesContext, period: int = 14) -> Series[Price]:
    """
    Relative Strength Index indicator using primitives.
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """
    if period <= 0:
        raise ValueError("RSI period must be positive")

    # Get price changes using diff primitive

    # Calculate price changes
    price_changes = diff(ctx)

    # Create contexts for gains and losses
    gains_ctx = SeriesContext(close=price_changes)
    losses_ctx = SeriesContext(close=price_changes)

    # Separate gains and losses
    gains = positive_values(gains_ctx)
    losses = negative_values(losses_ctx)

    # Calculate average gains and losses
    gains_avg_ctx = SeriesContext(close=gains)
    losses_avg_ctx = SeriesContext(close=losses)
    avg_gains = rolling_mean(gains_avg_ctx, period)
    avg_losses = rolling_mean(losses_avg_ctx, period)

    # Use expressions to calculate RSI
    # RS = avg_gains / avg_losses
    # RSI = 100 - (100 / (1 + RS))
    
    gains_expr = Expression(Literal(avg_gains))
    losses_expr = Expression(Literal(avg_losses))
    
    # RS = avg_gains / avg_losses (with epsilon to avoid division by zero)
    epsilon = 1e-10
    rs_expr = gains_expr / (losses_expr + epsilon)
    
    # RSI = 100 - (100 / (1 + RS))
    one_plus_rs = 1 + rs_expr
    rsi_ratio = 100 / one_plus_rs
    rsi_expr = 100 - rsi_ratio
    
    # Evaluate RSI
    context = {}
    return rsi_expr.evaluate(context)
