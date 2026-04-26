"""
signals.py - Buy / Sell / Hold Signal Generation
TRANALYZE – Trend Analyze

Combines MA crossovers, RSI thresholds, and pattern signals
into a final recommendation.
"""

import pandas as pd


# ─────────────────────────────────────────────────
# Thresholds
# ─────────────────────────────────────────────────

RSI_OVERSOLD    = 35   # RSI below this → bullish pressure
RSI_OVERBOUGHT  = 65   # RSI above this → bearish pressure
SCORE_BUY       = 2    # net bullish score to trigger BUY
SCORE_SELL      = -2   # net bearish score to trigger SELL


# ─────────────────────────────────────────────────
# Individual sub-signals
# ─────────────────────────────────────────────────

def _ma_signal(df: pd.DataFrame) -> int:
    """
    MA20 / MA50 crossover signal.
    +1 bullish if MA20 > MA50,  −1 bearish if MA20 < MA50
    """
    if "MA_20" not in df.columns or "MA_50" not in df.columns:
        return 0
    last = df.dropna(subset=["MA_20", "MA_50"]).tail(2)
    if len(last) < 2:
        return 0

    prev_cross = last.iloc[-2]["MA_20"] - last.iloc[-2]["MA_50"]
    curr_cross = last.iloc[-1]["MA_20"] - last.iloc[-1]["MA_50"]

    if prev_cross <= 0 and curr_cross > 0:
        return 2   # golden cross – strong buy
    if prev_cross >= 0 and curr_cross < 0:
        return -2  # death cross – strong sell
    return 1 if curr_cross > 0 else -1


def _rsi_signal(df: pd.DataFrame) -> int:
    """
    RSI threshold signal.
    +1 if oversold (potential reversal up), −1 if overbought.
    """
    if "RSI" not in df.columns:
        return 0
    rsi = df["RSI"].dropna()
    if rsi.empty:
        return 0

    val = rsi.iloc[-1]
    if val < RSI_OVERSOLD:
        return 1
    if val > RSI_OVERBOUGHT:
        return -1
    return 0


def _macd_signal(df: pd.DataFrame) -> int:
    """
    MACD histogram crossover signal.
    +1 if histogram flipped positive, −1 if negative.
    """
    if "MACD_Hist" not in df.columns:
        return 0
    hist = df["MACD_Hist"].dropna()
    if len(hist) < 2:
        return 0

    if hist.iloc[-2] < 0 and hist.iloc[-1] >= 0:
        return 1
    if hist.iloc[-2] > 0 and hist.iloc[-1] <= 0:
        return -1
    return 0


def _pattern_signal(patterns: dict) -> int:
    """
    Pattern-based signal from last candle.
    Bullish patterns → +1, Bearish patterns → −1.
    """
    bullish = {"Hammer", "Bullish Engulfing"}
    bearish = {"Shooting Star", "Bearish Engulfing"}
    score = 0
    for name, series in patterns.items():
        if series.any():
            last_hit = series[series].index[-1] if series.any() else None
            if last_hit is not None and last_hit == series.index[-1]:
                if name in bullish:
                    score += 1
                elif name in bearish:
                    score -= 1
    return score


# ─────────────────────────────────────────────────
# Master signal generator
# ─────────────────────────────────────────────────

def generate_signal(df: pd.DataFrame, patterns: dict) -> dict:
    """
    Aggregate all sub-signals into a final BUY / SELL / HOLD recommendation.

    Args:
        df:       OHLCV DataFrame with indicator columns attached
        patterns: dict of {pattern_name: bool Series} from patterns.py

    Returns:
        Dict with keys:
          - signal:    "BUY" | "SELL" | "HOLD"
          - score:     int (net bullish/bearish score)
          - reasons:   list of human-readable reason strings
          - sub:       dict of sub-signal breakdowns
    """
    ma_s      = _ma_signal(df)
    rsi_s     = _rsi_signal(df)
    macd_s    = _macd_signal(df)
    pattern_s = _pattern_signal(patterns)

    total = ma_s + rsi_s + macd_s + pattern_s

    reasons = []
    if ma_s > 0:
        reasons.append("MA20 above MA50 (bullish trend)")
    elif ma_s < 0:
        reasons.append("MA20 below MA50 (bearish trend)")

    if "RSI" in df.columns:
        rsi_val = df["RSI"].dropna().iloc[-1] if not df["RSI"].dropna().empty else None
        if rsi_val is not None:
            if rsi_s > 0:
                reasons.append(f"RSI {rsi_val:.1f} — oversold zone (potential upside)")
            elif rsi_s < 0:
                reasons.append(f"RSI {rsi_val:.1f} — overbought zone (potential pullback)")
            else:
                reasons.append(f"RSI {rsi_val:.1f} — neutral zone")

    if macd_s > 0:
        reasons.append("MACD histogram turned positive (bullish momentum)")
    elif macd_s < 0:
        reasons.append("MACD histogram turned negative (bearish momentum)")

    if pattern_s > 0:
        reasons.append("Bullish candlestick pattern detected on last candle")
    elif pattern_s < 0:
        reasons.append("Bearish candlestick pattern detected on last candle")

    if total >= SCORE_BUY:
        signal = "BUY"
    elif total <= SCORE_SELL:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "signal":  signal,
        "score":   total,
        "reasons": reasons,
        "sub": {
            "MA":      ma_s,
            "RSI":     rsi_s,
            "MACD":    macd_s,
            "Pattern": pattern_s,
        },
    }
