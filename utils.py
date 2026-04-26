import json
import os

# ─────────────────────────────────────────────────
# Market symbol format mappings
# ─────────────────────────────────────────────────

MARKET_CONFIG = {
    "NSE (India)": {
        "suffix": ".NS",
        "example": "HDFCBANK → HDFCBANK.NS",
        "placeholder": "e.g. HDFCBANK, RELIANCE, TCS",
        "default": "HDFCBANK",
    },
    "BSE (India)": {
        "suffix": ".BO",
        "example": "SBIN → SBIN.BO",
        "placeholder": "e.g. SBIN, INFY, WIPRO",
        "default": "SBIN",
    },
    "US Stocks": {
        "suffix": "",
        "example": "AAPL → AAPL",
        "placeholder": "e.g. AAPL, TSLA, GOOGL",
        "default": "AAPL",
    },
    "Forex": {
        "suffix": "=X",
        "example": "USDINR → USDINR=X",
        "placeholder": "e.g. USDINR, EURUSD, GBPUSD",
        "default": "USDINR",
    },
    "Crypto": {
        "suffix": "-USD",
        "example": "BTC → BTC-USD",
        "placeholder": "e.g. BTC, ETH, SOL",
        "default": "BTC",
    },
}

# ─────────────────────────────────────────────────
# Popular symbols for suggestions
# ─────────────────────────────────────────────────

POPULAR_SYMBOLS = {
    "NSE (India)": [
        "NIFTY_50", "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL",
        "SBIN", "LICI", "ITC", "HINDUNILVR", "LT", "BAJFINANCE", "ADANIENT", "MARUTI",
        "TITAN", "AXISBANK", "SUNPHARMA", "KOTAKBANK", "ASIANPAINT", "TATAMOTORS"
    ],
    "BSE (India)": [
        "SENSEX", "SBIN", "RELIANCE", "TCS", "INFY", "WIPRO", "HDFC", "TATAPOWER",
        "ZOMATO", "NYKAA", "PAYTM", "YESBANK", "IRFC", "JIOFIN", "TATASTEEL"
    ],
    "US Stocks": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "V",
        "JPM", "JNJ", "WMT", "MA", "PG", "NFLX", "AMD", "ADBE", "CRM", "NKE"
    ],
    "Forex": [
        "USDINR", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
        "EURGBP", "EURJPY", "GBPJPY", "NZDUSD"
    ],
    "Crypto": [
        "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK",
        "MATIC", "SHIB", "LTC", "PEPE", "NEAR", "STX"
    ],
}

# Timeframe → (yfinance interval, display label)
TIMEFRAME_MAP = {
    "1 Minute":  ("1m",  "1m"),
    "5 Minutes": ("5m",  "5m"),
    "15 Minutes":("15m", "15m"),
    "30 Minutes":("30m", "30m"),
    "1 Hour":    ("1h",  "1h"),
    "1 Day":     ("1d",  "1d"),
    "1 Week":    ("1wk", "1wk"),
    "1 Month":   ("1mo", "1mo"),
}

# Range → yfinance period
RANGE_MAP = {
    "1 Day":    "1d",
    "5 Days":   "5d",
    "1 Month":  "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year":   "1y",
    "2 Years":  "2y",
    "Max":      "max",
}

# Valid interval/period combinations (yfinance constraint)
VALID_COMBINATIONS = {
    "1m":  ["1d", "5d"],
    "5m":  ["1d", "5d", "1mo"],
    "15m": ["1d", "5d", "1mo"],
    "30m": ["1d", "5d", "1mo"],
    "1h":  ["1d", "5d", "1mo", "3mo"],
    "1d":  ["1mo", "3mo", "6mo", "1y", "2y", "max"],
    "1wk": ["3mo", "6mo", "1y", "2y", "max"],
    "1mo": ["6mo", "1y", "2y", "max"],
}


def convert_symbol(raw_symbol: str, market: str) -> str:
    """Convert a user-entered symbol to yfinance format based on market."""
    raw = raw_symbol.strip().upper()
    cfg = MARKET_CONFIG.get(market, {})
    suffix = cfg.get("suffix", "")

    if market == "Forex":
        # Already has =X or user typed raw pair
        return raw if raw.endswith("=X") else raw + suffix
    elif market == "Crypto":
        return raw if raw.endswith("-USD") else raw + suffix
    else:
        return raw if raw.endswith(suffix) else raw + suffix


def get_valid_ranges(interval: str) -> list:
    """Return valid range options for a given interval."""
    valid_periods = VALID_COMBINATIONS.get(interval, list(RANGE_MAP.values()))
    return [label for label, period in RANGE_MAP.items() if period in valid_periods]


def format_large_number(n) -> str:
    """Format large numbers into human-readable strings."""
    try:
        n = float(n)
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.2f}B"
        elif n >= 1_000_000:
            return f"{n/1_000_000:.2f}M"
        elif n >= 1_000:
            return f"{n/1_000:.2f}K"
        return f"{n:.2f}"
    except Exception:
        return "N/A"


def format_price(val, decimals: int = 2) -> str:
    """Format a price value safely."""
    try:
        return f"{float(val):.{decimals}f}"
    except Exception:
        return "N/A"


def pct_change(current, previous) -> float:
    """Calculate percentage change between two values."""
    try:
        return ((float(current) - float(previous)) / float(previous)) * 100
    except Exception:
        return 0.0


def get_all_symbols(market: str) -> list:
    """Load comprehensive symbols from local JSON if available, otherwise use hardcoded."""
    file_map = {
        "NSE (India)": "nse_symbols_list.json",
        "BSE (India)": "bse_symbols_list.json",
        "US Stocks":   "us_symbols_list.json",
        "Crypto":      "crypto_symbols_list.json",
        "Forex":       "forex_symbols_list.json",
    }
    
    filename = file_map.get(market)
    if filename and os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
            
    return POPULAR_SYMBOLS.get(market, [])
