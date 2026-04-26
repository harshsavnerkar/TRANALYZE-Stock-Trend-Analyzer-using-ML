"""
backtest.py - Simple Strategy Backtesting Module
TRANALYZE – Trend Analyze

Runs a Moving Average Crossover strategy on historical data
and returns performance metrics and trade log.
"""

import pandas as pd
import numpy as np


def run_ma_crossover_backtest(
    df: pd.DataFrame,
    fast_period: int = 20,
    slow_period: int = 50,
    initial_capital: float = 100_000.0
) -> dict:
    """
    Backtest a simple MA crossover strategy.

    Strategy:
        - BUY  when fast MA crosses above slow MA
        - SELL when fast MA crosses below slow MA

    Args:
        df:               OHLCV DataFrame
        fast_period:      fast MA window
        slow_period:      slow MA window
        initial_capital:  starting capital in currency units

    Returns:
        Dict with performance metrics and trade log DataFrame
    """
    if len(df) < slow_period + 10:
        return {"error": "Not enough data to run backtest."}

    df = df.copy()
    df["Fast_MA"] = df["Close"].rolling(fast_period).mean()
    df["Slow_MA"] = df["Close"].rolling(slow_period).mean()
    df.dropna(subset=["Fast_MA", "Slow_MA"], inplace=True)

    # Generate raw signals
    df["Signal"] = 0
    df.loc[df["Fast_MA"] > df["Slow_MA"], "Signal"] = 1   # bullish regime
    df["Position"] = df["Signal"].diff()                   # 1=buy, -1=sell

    # Simulate trades
    trades       = []
    cash         = initial_capital
    shares       = 0
    entry_price  = 0.0
    portfolio_value = []

    for i, row in df.iterrows():
        if row["Position"] == 1.0 and cash > 0:
            # BUY all-in
            shares      = cash / row["Close"]
            entry_price = row["Close"]
            cash        = 0.0
            trades.append({
                "Date":   i,
                "Action": "BUY",
                "Price":  round(row["Close"], 2),
                "Shares": round(shares, 4),
                "PnL":    0.0,
            })

        elif row["Position"] == -1.0 and shares > 0:
            # SELL all
            proceeds = shares * row["Close"]
            pnl      = proceeds - shares * entry_price
            trades.append({
                "Date":   i,
                "Action": "SELL",
                "Price":  round(row["Close"], 2),
                "Shares": round(shares, 4),
                "PnL":    round(pnl, 2),
            })
            cash   = proceeds
            shares = 0.0

        # Portfolio value at this point
        current_value = cash + shares * row["Close"]
        portfolio_value.append(current_value)

    # Close open position at last price
    if shares > 0:
        final_price  = df["Close"].iloc[-1]
        final_value  = cash + shares * final_price
    else:
        final_value  = cash

    trades_df = pd.DataFrame(trades)

    total_return    = ((final_value - initial_capital) / initial_capital) * 100
    total_pnl       = final_value - initial_capital
    n_trades        = len(trades_df)
    n_wins          = (trades_df["PnL"] > 0).sum() if not trades_df.empty else 0
    win_rate        = (n_wins / (n_trades / 2) * 100) if n_trades > 0 else 0

    # Max drawdown
    portfolio_series = pd.Series(portfolio_value, index=df.index[:len(portfolio_value)])
    rolling_max      = portfolio_series.cummax()
    drawdowns        = (portfolio_series - rolling_max) / rolling_max * 100
    max_drawdown     = drawdowns.min()

    return {
        "initial_capital":  initial_capital,
        "final_value":      round(final_value, 2),
        "total_pnl":        round(total_pnl, 2),
        "total_return_pct": round(total_return, 2),
        "n_trades":         n_trades,
        "win_rate_pct":     round(win_rate, 1),
        "max_drawdown_pct": round(max_drawdown, 2),
        "trades":           trades_df,
        "portfolio_series": portfolio_series,
    }
