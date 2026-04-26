import pandas as pd
import numpy as np

# Helper functions for calculations
def _body(df): return (df["Close"] - df["Open"]).abs()
def _range(df): return df["High"] - df["Low"]
def _upper_shadow(df): return df["High"] - df[["Open", "Close"]].max(axis=1)
def _lower_shadow(df): return df[["Open", "Close"]].min(axis=1) - df["Low"]

# ── Candlestick Patterns ────────────────────────

def detect_doji(df):
    body = _body(df)
    rng = _range(df).replace(0, np.nan)
    return (body / rng) < 0.1

def detect_hammer(df):
    body = _body(df)
    rng = _range(df).replace(0, np.nan)
    lower_s = _lower_shadow(df)
    upper_s = _upper_shadow(df)
    return (body / rng < 0.3) & (lower_s > 2 * body) & (upper_s < body)

def detect_hanging_man(df):
    # Occurs at the top of an uptrend
    body = _body(df)
    rng = _range(df).replace(0, np.nan)
    lower_s = _lower_shadow(df)
    upper_s = _upper_shadow(df)
    return (body / rng < 0.3) & (lower_s > 2 * body) & (upper_s < body)

def detect_shooting_star(df):
    body = _body(df)
    rng = _range(df).replace(0, np.nan)
    lower_s = _lower_shadow(df)
    upper_s = _upper_shadow(df)
    return (body / rng < 0.3) & (upper_s > 2 * body) & (lower_s < body)

def detect_inverted_hammer(df):
    body = _body(df)
    rng = _range(df).replace(0, np.nan)
    lower_s = _lower_shadow(df)
    upper_s = _upper_shadow(df)
    return (body / rng < 0.3) & (upper_s > 2 * body) & (lower_s < body)

def detect_bullish_engulfing(df):
    prev_bear = df["Close"].shift(1) < df["Open"].shift(1)
    curr_bull = df["Close"] > df["Open"]
    engulfs = (df["Open"] < df["Close"].shift(1)) & (df["Close"] > df["Open"].shift(1))
    return prev_bear & curr_bull & engulfs

def detect_bearish_engulfing(df):
    prev_bull = df["Close"].shift(1) > df["Open"].shift(1)
    curr_bear = df["Close"] < df["Open"]
    engulfs = (df["Open"] > df["Close"].shift(1)) & (df["Close"] < df["Open"].shift(1))
    return prev_bull & curr_bear & engulfs

def detect_morning_star(df):
    if len(df) < 3: return pd.Series(False, index=df.index)
    c1 = df["Close"].shift(2) < df["Open"].shift(2)
    c2 = detect_doji(df.shift(1))
    c3 = df["Close"] > df["Open"]
    return c1 & c2 & c3

def detect_evening_star(df):
    if len(df) < 3: return pd.Series(False, index=df.index)
    c1 = df["Close"].shift(2) > df["Open"].shift(2)
    c2 = detect_doji(df.shift(1))
    c3 = df["Close"] < df["Open"]
    return c1 & c2 & c3

def detect_three_white_soldiers(df):
    if len(df) < 3: return pd.Series(False, index=df.index)
    c1 = df["Close"].shift(2) > df["Open"].shift(2)
    c2 = df["Close"].shift(1) > df["Open"].shift(1)
    c3 = df["Close"] > df["Open"]
    higher_c = (df["Close"] > df["Close"].shift(1)) & (df["Close"].shift(1) > df["Close"].shift(2))
    return c1 & c2 & c3 & higher_c

def detect_three_black_crows(df):
    if len(df) < 3: return pd.Series(False, index=df.index)
    c1 = df["Close"].shift(2) < df["Open"].shift(2)
    c2 = df["Close"].shift(1) < df["Open"].shift(1)
    c3 = df["Close"] < df["Open"]
    lower_c = (df["Close"] < df["Close"].shift(1)) & (df["Close"].shift(1) < df["Close"].shift(2))
    return c1 & c2 & c3 & lower_c

def detect_piercing_pattern(df):
    if len(df) < 2: return pd.Series(False, index=df.index)
    prev_bear = df["Close"].shift(1) < df["Open"].shift(1)
    curr_bull = df["Close"] > df["Open"]
    midpoint = (df["Open"].shift(1) + df["Close"].shift(1)) / 2
    return prev_bear & curr_bull & (df["Open"] < df["Low"].shift(1)) & (df["Close"] > midpoint)

def detect_dark_cloud_cover(df):
    if len(df) < 2: return pd.Series(False, index=df.index)
    prev_bull = df["Open"].shift(1) < df["Close"].shift(1)
    curr_bear = df["Open"] > df["Close"]
    midpoint = (df["Open"].shift(1) + df["Close"].shift(1)) / 2
    return prev_bull & curr_bear & (df["Open"] > df["High"].shift(1)) & (df["Close"] < midpoint)

def detect_spinning_top(df):
    body = _body(df)
    rng = _range(df).replace(0, np.nan)
    return (body / rng > 0.1) & (body / rng < 0.3)

def detect_marubozu(df):
    body = _body(df)
    rng = _range(df).replace(0, np.nan)
    return (body / rng) > 0.95

# ── Master Detection Function ─────────────────

def detect_all_patterns(df):
    patterns = {
        "Doji": detect_doji(df),
        "Hammer": detect_hammer(df),
        "Hanging Man": detect_hanging_man(df),
        "Shooting Star": detect_shooting_star(df),
        "Inverted Hammer": detect_inverted_hammer(df),
        "Bullish Engulfing": detect_bullish_engulfing(df),
        "Bearish Engulfing": detect_bearish_engulfing(df),
        "Morning Star": detect_morning_star(df),
        "Evening Star": detect_evening_star(df),
        "Three White Soldiers": detect_three_white_soldiers(df),
        "Three Black Crows": detect_three_black_crows(df),
        "Piercing Pattern": detect_piercing_pattern(df),
        "Dark Cloud Cover": detect_dark_cloud_cover(df),
        "Spinning Top": detect_spinning_top(df),
        "Marubozu": detect_marubozu(df),
    }
    return {k: v.fillna(False) for k, v in patterns.items()}


def get_pattern_summary(df: pd.DataFrame) -> list:
    """Return a list of dicts summarising the last 30 candles' patterns."""
    patterns  = detect_all_patterns(df)
    recent_df = df.tail(30)
    events    = []

    for name, series in patterns.items():
        hits = series[series].index.intersection(recent_df.index)
        for idx in hits:
            events.append({
                "date":      idx,
                "pattern":   name,
                "sentiment": "Neutral", # Simplified for now
                "close":     df.loc[idx, "Close"],
            })

    events.sort(key=lambda x: x["date"], reverse=True)
    return events
