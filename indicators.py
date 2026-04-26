"""
indicators.py - Technical Indicators Engine
TRANALYZE – Trend Analyze

Calculates: Moving Averages, RSI, MACD, Bollinger Bands
All functions accept a DataFrame and return a modified copy.
"""

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────
# Moving Averages
# ─────────────────────────────────────────────────

def add_moving_averages(df: pd.DataFrame,
                        periods: list = [20, 50, 200]) -> pd.DataFrame:
    """
    Add Simple Moving Averages to the DataFrame.

    Args:
        df:      OHLCV DataFrame
        periods: list of MA window sizes

    Returns:
        DataFrame with additional MA columns (e.g. MA_20, MA_50, MA_200)
    """
    df = df.copy()
    for p in periods:
        if len(df) >= p:
            df[f"MA_{p}"] = df["Close"].rolling(window=p).mean()
    return df


# ─────────────────────────────────────────────────
# RSI – Relative Strength Index
# ─────────────────────────────────────────────────

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate RSI using Wilder's smoothing method.

    Args:
        df:     OHLCV DataFrame
        period: lookback window (default 14)

    Returns:
        DataFrame with 'RSI' column (0–100 scale)
    """
    df = df.copy()
    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


# ─────────────────────────────────────────────────
# MACD – Moving Average Convergence Divergence
# ─────────────────────────────────────────────────

def add_macd(df: pd.DataFrame,
             fast: int = 12,
             slow: int = 26,
             signal: int = 9) -> pd.DataFrame:
    """
    Calculate MACD line, Signal line, and Histogram.

    Args:
        df:     OHLCV DataFrame
        fast:   fast EMA period (default 12)
        slow:   slow EMA period (default 26)
        signal: signal EMA period (default 9)

    Returns:
        DataFrame with 'MACD', 'MACD_Signal', 'MACD_Hist' columns
    """
    df = df.copy()
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()

    df["MACD"]        = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]

    return df


# ─────────────────────────────────────────────────
# Bollinger Bands
# ─────────────────────────────────────────────────

def add_bollinger_bands(df: pd.DataFrame,
                        period: int = 20,
                        std_dev: float = 2.0) -> pd.DataFrame:
    """
    Calculate Bollinger Bands: upper, middle (SMA), and lower bands.

    Args:
        df:      OHLCV DataFrame
        period:  rolling window for SMA (default 20)
        std_dev: number of standard deviations (default 2)

    Returns:
        DataFrame with 'BB_Upper', 'BB_Middle', 'BB_Lower' columns
    """
    df = df.copy()
    sma   = df["Close"].rolling(window=period).mean()
    sigma = df["Close"].rolling(window=period).std()

    df["BB_Middle"] = sma
    df["BB_Upper"]  = sma + std_dev * sigma
    df["BB_Lower"]  = sma - std_dev * sigma

    return df


# ─────────────────────────────────────────────────
# Combined indicator application
# ─────────────────────────────────────────────────

def apply_all_indicators(df: pd.DataFrame,
                          show_ma: bool = True,
                          show_rsi: bool = True,
                          show_macd: bool = True,
                          show_bb: bool = True) -> pd.DataFrame:
    """
    Apply all selected indicators to the DataFrame.

    Args:
        df:        OHLCV DataFrame
        show_ma:   include moving averages
        show_rsi:  include RSI
        show_macd: include MACD
        show_bb:   include Bollinger Bands

    Returns:
        DataFrame enriched with selected indicator columns
    """
    if show_ma:
        df = add_moving_averages(df, periods=[20, 50, 200])
    if show_rsi:
        df = add_rsi(df)
    if show_macd:
        df = add_macd(df)
    if show_bb:
        df = add_bollinger_bands(df)
    return df
