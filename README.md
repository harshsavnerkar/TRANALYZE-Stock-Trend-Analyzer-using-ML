# 📈 TRANALYZE – Trend Analyze

> **A professional trading analysis dashboard for educational purposes.**  
> Inspired by Zerodha Kite and TradingView. Built with Python + Streamlit.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌍 Multi-market | NSE, BSE, US Stocks, Forex, Crypto |
| 📊 Interactive Charts | Candlestick with zoom, pan, hover (Plotly) |
| 📐 Technical Indicators | MA (20/50/200), RSI, MACD, Bollinger Bands |
| 🕯️ Pattern Detection | Doji, Hammer, Shooting Star, Engulfing candles |
| 🎯 Signal Engine | BUY / SELL / HOLD based on multi-factor scoring |
| 🤖 ML Prediction | Linear Regression & Random Forest next-close predictor |
| ⏱️ Backtesting | MA Crossover strategy with equity curve & trade log |
| 📋 Watchlist | Save & track your favourite symbols |
| ⬇️ Data Export | Download OHLCV + indicator data as CSV |

---

## 🗂️ Project Structure

```
tranalyze/
├── app.py          ← Main Streamlit UI (entry point)
├── data.py         ← yfinance data fetching & caching
├── indicators.py   ← Technical indicators (MA, RSI, MACD, BB)
├── patterns.py     ← Candlestick pattern detection
├── signals.py      ← BUY/SELL/HOLD signal generation
├── model.py        ← ML prediction engine
├── backtest.py     ← MA crossover backtesting
├── chart.py        ← Plotly chart builder
├── utils.py        ← Symbol conversion & helper utilities
└── requirements.txt
```

---

## 🚀 Setup & Installation

### 1. Clone / Download
```bash
git clone <your-repo-url>
cd tranalyze
```

### 2. Create virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate.bat       # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

The dashboard opens automatically at **http://localhost:8501**

---

## 🎮 Usage

### Selecting a Market & Symbol

| Market | Example Input | Converted To |
|--------|--------------|-------------|
| NSE (India) | `HDFCBANK` | `HDFCBANK.NS` |
| BSE (India) | `SBIN` | `SBIN.BO` |
| US Stocks | `AAPL` | `AAPL` |
| Forex | `USDINR` | `USDINR=X` |
| Crypto | `BTC` | `BTC-USD` |

### Timeframe & Range Combinations

| Timeframe | Valid Ranges |
|-----------|-------------|
| 1m, 5m, 15m, 30m | 1 Day, 5 Days |
| 1h | Up to 3 Months |
| 1d | Up to Max |
| 1wk, 1mo | 3 Months to Max |

### Technical Indicators

- **MA 20/50/200** — Simple Moving Averages. Crossovers signal trend changes.
- **RSI (14)** — Relative Strength Index. Below 35 = oversold, above 65 = overbought.
- **MACD (12/26/9)** — Momentum. Histogram crossovers signal shifts.
- **Bollinger Bands (20, 2σ)** — Volatility bands. Price touching bands signals extremes.

### Signal Engine

Signals are scored on a scale of −5 to +5:
- **BUY** (score ≥ +2): MA crossover bullish + RSI oversold + MACD positive + bullish pattern
- **SELL** (score ≤ −2): Opposite conditions
- **HOLD**: Mixed or neutral signals

### ML Price Prediction

The model engineers features (prev close, moving averages, price change, volume) and trains on 80% of historical data. R² and MAE are reported on the test set. The last candle's features predict the *next* candle's close.

### Backtesting

The MA Crossover strategy:
- **BUY** when Fast MA crosses above Slow MA
- **SELL** when Fast MA crosses below Slow MA
- Reports: Final value, Total P&L, Win Rate, Max Drawdown, Trade Log, Equity Curve

---

## ⚠️ Disclaimer

TRANALYZE is built **strictly for educational and analytical purposes**.  
It does **not** execute real trades, connect to any brokerage, or provide financial advice.  
Always consult a qualified financial advisor before making investment decisions.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** — Web UI framework
- **yfinance** — Market data API (Yahoo Finance)
- **Pandas / NumPy** — Data processing
- **Plotly** — Interactive charting
- **scikit-learn** — Machine learning models

---

## 📄 License

MIT License — Free to use, modify, and distribute for non-commercial purposes.
