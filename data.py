"""
data.py - Data Fetching and Cleaning Module
TRANALYZE – Trend Analyze
"""

import yfinance as yf
import pandas as pd
import streamlit as st


@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_data(symbol: str, interval: str, period: str) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance.

    Args:
        symbol:   yfinance-formatted ticker (e.g. 'HDFCBANK.NS')
        interval: data granularity (e.g. '1d', '1h', '15m')
        period:   historical range  (e.g. '1y', '3mo')

    Returns:
        Cleaned DataFrame with columns: Open, High, Low, Close, Volume
        Returns empty DataFrame on failure.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if df is None or df.empty:
            return pd.DataFrame()

        # Keep only relevant columns
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()

        # Drop rows where all OHLC are NaN
        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)

        # Force convert to Indian Standard Time (IST) for consistency
        if df.index.tz is not None:
            df.index = df.index.tz_convert("Asia/Kolkata").tz_localize(None)
        else:
            # If no TZ, assume it might be UTC and convert if it's a global market
            # But for safety, we just ensure it's clean for Plotly
            df.index = df.index.tz_localize(None)
            
        return df

    except Exception as e:
        return pd.DataFrame()


def fetch_ticker_info(symbol: str) -> dict:
    """
    Fetch ticker metadata (name, sector, market cap, etc.).

    Args:
        symbol: yfinance-formatted ticker

    Returns:
        Dict with ticker info, empty dict on failure.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        return {
            "name":        info.get("longName") or info.get("shortName", symbol),
            "sector":      info.get("sector", "—"),
            "market_cap":  info.get("marketCap", None),
            "currency":    info.get("currency", ""),
            "exchange":    info.get("exchange", ""),
            "52w_high":    info.get("fiftyTwoWeekHigh", None),
            "52w_low":     info.get("fiftyTwoWeekLow", None),
            "pe_ratio":    info.get("trailingPE", None),
            "dividend":    info.get("dividendYield", None),
        }
    except Exception:
        return {}


def get_summary_metrics(df: pd.DataFrame) -> dict:
    """
    Extract key summary metrics from a OHLCV DataFrame.

    Args:
        df: Cleaned OHLCV DataFrame

    Returns:
        Dict with current_price, prev_close, pct_change, period_high,
        period_low, volume.
    """
    if df.empty:
        return {}

    current_price = df["Close"].iloc[-1]
    prev_close    = df["Close"].iloc[-2] if len(df) > 1 else current_price
    pct_chg       = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0
    period_high   = df["High"].max()
    period_low    = df["Low"].min()
    volume        = df["Volume"].iloc[-1]

    return {
        "current_price": current_price,
        "prev_close":    prev_close,
        "pct_change":    pct_chg,
        "period_high":   period_high,
        "period_low":    period_low,
        "volume":        volume,
        "open":          df["Open"].iloc[-1],
    }
