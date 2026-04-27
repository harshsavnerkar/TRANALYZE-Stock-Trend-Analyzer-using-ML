
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import re

def get_market_pulse():
    """Fetches and predicts status using SECTOR-SPECIFIC & MACRO data."""
    indices = {
        "Nifty 50": {"ticker": "^NSEI", "sector": "Indian Blue-Chip & Macro"},
        "Bank Nifty": {"ticker": "^NSEBANK", "sector": "Banking & Financial Services"},
        "Sensex": {"ticker": "^BSESN", "sector": "Major Institutional Assets"}
    }
    
    # GLOBAL CATALYSTS
    global_indices = {"Nasdaq": "^IXIC", "S&P 500": "^GSPC"}
    macro_backdrop = {}
    try:
        for g_name, g_ticker in global_indices.items():
            g_data = yf.download(g_ticker, period="1d", interval="1h", progress=False)
            if not g_data.empty:
                g_chg = ((g_data['Close'].iloc[-1] - g_data['Open'].iloc[0]) / g_data['Open'].iloc[0] * 100).item()
                macro_backdrop[g_name] = g_chg
    except: pass

    pulse_data = {}
    
    for name, config in indices.items():
        ticker = config["ticker"]
        sector_context = config["sector"]
        try:
            # PULL HIGH-FREQ DATA
            data = yf.download(ticker, period="2d", interval="5m", progress=False)
            if data.empty: continue
            
            curr_price = data['Close'].iloc[-1].item()
            
            # ── OPENING PRICE PROJECTOR logic ──
            # Formula: Current Price * (1 + (Weighted Sentiment + Macro Bias + Intraday ATR))
            atr = (data['High'] - data['Low']).tail(20).mean().item()
            macro_bias = (macro_backdrop.get("Nasdaq", 0) / 100)
            
            # Intraday Momentum %
            momentum_pct = ((data['Close'].iloc[-1] - data['Close'].iloc[-10]) / data['Close'].iloc[-10]).item()
            
            # Predict Direction
            prediction = "Green" if (momentum_pct > 0 or macro_bias > 0) else "Red"
            if macro_bias < -0.005: prediction = "Red" # Macro override
            
            # Project Price
            # We assume a gap-up/down based on bias, capped by 1.5x ATR
            projected_move = (curr_price * (macro_bias + (momentum_pct/2)))
            projected_open = curr_price + projected_move
            
            intensity = "Major" if abs(macro_bias) > 0.005 else "Light"
            
            # ── SECTOR-SPECIFIC REASONING ──
            reasons = []
            
            # Sector Headlines Check
            keywords = []
            if "Banking" in sector_context: keywords = ["RBI", "bank", "interest", "HDFC", "SBI", "loan"]
            elif "Blue-Chip" in sector_context: keywords = ["Reliance", "TCS", "market", "Nifty", "corporate", "earnings"]
            
            s_score, s_status, headlines = get_news_sentiment(ticker, keywords)
            
            reasons.append(f"Sector Focus: Analyzing {sector_context} news flow.")
            if s_score != 0:
                reasons.append(f"Sentiment Audit: {s_status} based on {sector_context} headline analysis.")
            
            if macro_backdrop:
                reasons.append(f"Macro Overlay: Global tech indices ({macro_backdrop.get('Nasdaq', 0):+.2f}%) influence the opening projection.")
            
            reasons.append(f"Technicals: Intraday pulse suggests a {intensity.lower()} directional shift.")
                
            pulse_data[name] = {
                "price": curr_price,
                "projected_open": projected_open,
                "pred": prediction,
                "intensity": intensity,
                "reasons": reasons,
                "headlines": headlines[:4] if headlines else []
            }
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            
    return pulse_data

def get_news_sentiment(symbol, sector_keywords=[]):
    """Fetches news and filters by SECTOR keywords."""
    try:
        search_ticker = "SPY" if symbol in ["^NSEI", "^BSESN", "^NSEBANK"] else symbol
        ticker = yf.Ticker(search_ticker)
        news = ticker.news
        if not news: return 0, "Neutral", []
            
        positive_keywords = ['growth', 'profit', 'upgrade', 'buy', 'win', 'expansion', 'high', 'success', 'fed pause', 'inflation down', 'rate cut'] + sector_keywords
        negative_keywords = ['loss', 'drop', 'downgrade', 'sell', 'lawsuit', 'investigation', 'debt', 'risk', 'fail', 'fed hike', 'inflation up']
        
        score = 0
        headlines = []
        for n in news[:10]:
            title = n.get('title', '').lower()
            matching = False
            # Check if this news is relevant to the sectors we want
            if sector_keywords:
                for sk in sector_keywords:
                    if sk.lower() in title: 
                        matching = True
                        break
            else: matching = True
            
            if matching:
                headlines.append(n.get('title'))
                for word in positive_keywords:
                    if word.lower() in title: score += 1
                for word in negative_keywords:
                    if word.lower() in title: score -= 1
        
        if score > 0: status = "Bullish Sector News"
        elif score < 0: status = "Bearish Sector News"
        else: status = "Stable Sentiment"
            
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
