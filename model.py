"""
model.py - Machine Learning Prediction Engine
TRANALYZE – Trend Analyze

Uses Linear Regression (and optionally Random Forest) to predict
the next closing price based on engineered features.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score


# ─────────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create ML features from raw OHLCV data.

    Features:
        - prev_close:   previous candle's Close
        - price_change: Close - prev_close
        - high_low_diff: High - Low (volatility proxy)
        - open_close_diff: Close - Open (body size)
        - ma_20, ma_50: Moving averages (if available)
        - volume_change: % change in volume

    Returns:
        DataFrame with feature and target columns.
        Target = 'next_close' (the next candle's Close)
    """
    f = pd.DataFrame(index=df.index)

    f["prev_close"]      = df["Close"].shift(1)
    f["price_change"]    = df["Close"] - df["Close"].shift(1)
    f["high_low_diff"]   = df["High"] - df["Low"]
    f["open_close_diff"] = df["Close"] - df["Open"]
    f["volume"]          = df["Volume"]
    f["volume_change"]   = df["Volume"].pct_change()

    if "MA_20" in df.columns:
        f["ma_20"] = df["MA_20"]
    else:
        f["ma_20"] = df["Close"].rolling(20).mean()

    if "MA_50" in df.columns:
        f["ma_50"] = df["MA_50"]
    else:
        f["ma_50"] = df["Close"].rolling(50).mean()

    f["rsi"] = df.get("RSI", pd.Series(np.nan, index=df.index))

    # Target: next candle's closing price
    f["next_close"] = df["Close"].shift(-1)

    f.dropna(inplace=True)
    return f


# ─────────────────────────────────────────────────
# Model Training & Prediction
# ─────────────────────────────────────────────────

FEATURE_COLS = [
    "prev_close", "price_change", "high_low_diff",
    "open_close_diff", "volume_change", "ma_20", "ma_50", "rsi"
]


def train_and_predict(df: pd.DataFrame,
                      model_type: str = "Linear Regression") -> dict:
    """
    Train a regression model on historical data and predict the next close.

    Args:
        df:         OHLCV DataFrame (with indicator columns if available)
        model_type: "Linear Regression" or "Random Forest"

    Returns:
        Dict with:
          - predicted_price: float
          - mae:             Mean Absolute Error on test set
          - r2:              R² score on test set
          - model_type:      str
          - confidence:      "High" | "Medium" | "Low"
          - feature_importance: dict (Random Forest only)
    """
    feat_df = engineer_features(df)

    # Need at least 50 rows for meaningful training
    if len(feat_df) < 50:
        return {"error": "Not enough data for ML prediction (need ≥ 50 candles)."}

    # Use available feature columns
    available_features = [c for c in FEATURE_COLS if c in feat_df.columns]

    # Replace inf/-inf with NaN, then drop any remaining NaN rows
    feat_df[available_features] = feat_df[available_features].replace(
        [np.inf, -np.inf], np.nan
    )
    feat_df.dropna(subset=available_features + ["next_close"], inplace=True)

    if len(feat_df) < 50:
        return {"error": "Not enough clean data for ML prediction after removing invalid rows."}

    X = feat_df[available_features].values
    y = feat_df["next_close"].values

    # Train / test split (80/20, no shuffle – time series)
    split = max(1, int(len(X) * 0.8))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Scale features
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # Choose model
    if model_type == "Random Forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42)
    else:
        model = LinearRegression()

    model.fit(X_train_s, y_train)

    # Evaluate
    preds    = model.predict(X_test_s)
    mae      = mean_absolute_error(y_test, preds)
    r2       = r2_score(y_test, preds)

    # Predict next closing price using the most recent candle
    last_features = scaler.transform([X[-1]])
    predicted_price = float(model.predict(last_features)[0])

    # Confidence heuristic based on R²
    if r2 >= 0.85:
        confidence = "High"
    elif r2 >= 0.65:
        confidence = "Medium"
    else:
        confidence = "Low"

    result = {
        "predicted_price":    predicted_price,
        "mae":                mae,
        "r2":                 r2,
        "model_type":         model_type,
        "confidence":         confidence,
        "feature_importance": {},
    }

    # Feature importance for Random Forest
    if model_type == "Random Forest":
        importances = model.feature_importances_
        result["feature_importance"] = dict(
            zip(available_features, [round(i * 100, 2) for i in importances])
        )

    return result