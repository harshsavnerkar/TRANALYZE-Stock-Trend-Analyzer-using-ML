
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import re

def get_market_pulse():
    """Fetches and predicts status for major Indian indices using GLOBAL MACRO INTELLIGENCE."""
    indices = {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "Sensex": "^BSESN"
    }
    
    # GLOBAL CATALYSTS (US Markets reach Indian Sentiment)
    global_indices = {
        "Nasdaq": "^IXIC",
        "S&P 500": "^GSPC",
        "US 10Y Yield": "^TNX"
    }
    
    macro_backdrop = {}
    try:
        for g_name, g_ticker in global_indices.items():
            g_data = yf.download(g_ticker, period="2d", interval="1h", progress=False)
            if not g_data.empty:
                g_chg = ((g_data['Close'].iloc[-1] - g_data['Open'].iloc[0]) / g_data['Open'].iloc[0] * 100).item()
                macro_backdrop[g_name] = g_chg
    except: pass

    pulse_data = {}
    
    for name, ticker in indices.items():
        try:
            # PULL DATA
            data = yf.download(ticker, period="1d", interval="1m", progress=False)
            if data.empty: continue
            
            curr_price = data['Close'].iloc[-1].item()
            prev_price = data['Close'].iloc[-2].item() if len(data) > 1 else curr_price
            change = curr_price - prev_price
            pct_change = (change / prev_price) * 100 if prev_price != 0 else 0
            
            # ── GLOBAL INTELLIGENCE WEIGHTING ──
            # If Nasdaq is up > 1%, it adds +1 to our Bullish Bias
            macro_score = 0
            if macro_backdrop.get("Nasdaq", 0) > 0.5: macro_score += 1
            if macro_backdrop.get("Nasdaq", 0) < -0.5: macro_score -= 1
            if macro_backdrop.get("S&P 500", 0) > 0.5: macro_score += 1
            
            # Intraday Momentum
            momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-15]).item() if len(data) > 15 else (data['Close'].iloc[-1] - data['Close'].iloc[0]).item()
            
            # Final Prediction (Macro + Momentum)
            prediction = "Green" if (momentum > 0 or macro_score > 0) else "Red"
            if macro_score < -1: prediction = "Red" # Macro override
            
            intensity = "Major" if abs(pct_change) > 0.6 else "Light"
            
            # ── REASONING ENGINE (GLOBAL MACRO FOCUS) ──
            reasons = []
            
            # 1. Macro Backdrop
            if macro_backdrop:
                nasdaq_status = "Rallying" if macro_backdrop.get("Nasdaq", 0) > 0 else "Slumping"
                reasons.append(f"Global Catalyst: {nasdaq_status} US tech markets (Nasdaq {macro_backdrop.get('Nasdaq', 0):+.2f}%) providing a {'Bullish' if nasdaq_status=='Rallying' else 'Bearish'} worldwide backdrop.")
            
            # 2. News Pulse
            s_score, s_status, headlines = get_news_sentiment(ticker)
            if s_score != 0:
                reasons.append(f"Fundamental Sentiment: {s_status} active based on global headline audit.")
            
            # 3. Technical Pressure
            if momentum > 0: reasons.append("Price Action: Intraday charts show sustained buyer accumulation in recent minutes.")
            else: reasons.append("Price Action: Intraday charts indicate aggressive profit-booking and distribution.")
            
            if abs(pct_change) > 1.0:
                reasons.append(f"Volatility Alert: Index is moving with high institutional intensity ({abs(pct_change):.2f}%).")
                
            pulse_data[name] = {
                "price": curr_price,
                "change": change,
                "pct": pct_change,
                "pred": prediction,
                "intensity": intensity,
                "reasons": reasons,
                "headlines": headlines[:3] if headlines else []
            }
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            
    return pulse_data

def get_news_sentiment(symbol):
    """Fetches global news and analyzes sentiment."""
    try:
        # Use a broader ticker for indices or global context
        search_ticker = "SPY" if symbol in ["^NSEI", "^BSESN", "^NSEBANK"] else symbol
        ticker = yf.Ticker(search_ticker)
        news = ticker.news
        if not news:
            return 0, "Neutral", []
            
        positive_keywords = ['growth', 'profit', 'upgrade', 'buy', 'win', 'expansion', 'high', 'success', 'fed pause', 'inflation down', 'rate cut']
        negative_keywords = ['loss', 'drop', 'downgrade', 'sell', 'lawsuit', 'investigation', 'debt', 'risk', 'fail', 'fed hike', 'inflation up']
        
        score = 0
        headlines = []
        for n in news[:8]: # Analyze more headlines for 'Worldwide' context
            title = n.get('title', '').lower()
            headlines.append(n.get('title'))
            for word in positive_keywords:
                if word in title: score += 1
            for word in negative_keywords:
                if word in title: score -= 1
        
        if score > 0: status = "Bullish News"
        elif score < 0: status = "Bearish News"
        else: status = "Neutral/Mixed"
            
        return score, status, headlines
    except:
        return 0, "Market Neutral", []

def get_google_price(symbol, market):
    try:
        exchange_map = {"NSE": "NSE", "BSE": "BOM", "US Stocks": "NASDAQ", "Crypto": "CURRENCY", "Forex": "CURRENCY"}
        exch = exchange_map.get(market, "NSE")
        if market == "US Stocks" and ".N" in symbol: exch = "NYSE"
        clean_sym = symbol.split('.')[0]
        url = f"https://www.google.com/finance/quote/{clean_sym}:{exch}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        match = re.search(r'data-last-price="([\d\.,]+)"', response.text)
        if match: return float(match.group(1).replace(',', ''))
        return None
    except: return None
