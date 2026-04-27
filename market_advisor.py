
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import re

def get_market_pulse():
    """Fetches and predicts status for major Indian indices."""
    indices = {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "Sensex": "^BSESN"
    }
    
    pulse_data = {}
    
    for name, ticker in indices.items():
        try:
            # PULL 1M DATA FOR MAXIMUM ACCURACY
            data = yf.download(ticker, period="1d", interval="1m", progress=False)
            if data.empty: continue
            
            curr_price = data['Close'].iloc[-1].item()
            prev_price = data['Close'].iloc[-2].item() if len(data) > 1 else curr_price
            change = curr_price - prev_price
            pct_change = (change / prev_price) * 100 if prev_price != 0 else 0
            
            # Simple Prediction Logic based on Momentum and Volatility
            # Next Day Prediction (Green/Red) + Intensity
            # We look at the last 15 minutes of intensity
            momentum = (data['Close'].iloc[-1] - data['Close'].iloc[-15]).item() if len(data) > 15 else (data['Close'].iloc[-1] - data['Close'].iloc[0]).item()
            avg_vol = data['Volume'].mean().item()
            curr_vol = data['Volume'].iloc[-1].item()
            
            prediction = "Green" if momentum > 0 else "Red"
            
            # Intensity based on 2nd standard deviation of 5-day range
            day_range = (data['High'] - data['Low']).mean().item()
            intensity_val = abs(change) / day_range if day_range != 0 else 0
            
            if intensity_val > 1.2:
                intensity = "Major"
            else:
                intensity = "Light"
                
            pulse_data[name] = {
                "price": curr_price,
                "change": change,
                "pct": pct_change,
                "pred": prediction,
                "intensity": intensity
            }
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            
    return pulse_data

def get_news_sentiment(symbol):
    """Fetches recent news and analyzes sentiment."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return 0, "Neutral" # Score 0, Neutral
            
        positive_keywords = ['growth', 'profit', 'upgrade', 'buy', 'win', 'expansion', 'high', 'success', 'dividend', 'deal']
        negative_keywords = ['loss', 'drop', 'downgrade', 'sell', 'lawsuit', 'investigation', 'debt', 'risk', 'fail', 'crash']
        
        score = 0
        headlines = []
        for n in news[:5]: # Analyze last 5 headlines
            title = n.get('title', '').lower()
            headlines.append(n.get('title'))
            for word in positive_keywords:
                if word in title: score += 1
            for word in negative_keywords:
                if word in title: score -= 1
        
        if score > 0:
            status = "Bullish News"
        elif score < 0:
            status = "Bearish News"
        else:
            status = "Neutral/No Impact"
            
        return score, status, headlines
    except:
        return 0, "No News", []

def get_google_price(symbol, market):
    """
    Scrapes the real-time price from Google Finance as a verification source.
    """
    try:
        # Map markets to Google Finance exchanges
        exchange_map = {
            "NSE": "NSE",
            "BSE": "BOM",
            "US Stocks": "NASDAQ",
            "Crypto": "CURRENCY",
            "Forex": "CURRENCY"
        }
        
        exch = exchange_map.get(market, "NSE")
        # Handle NYSE vs NASDAQ for US
        if market == "US Stocks" and ".N" in symbol: exch = "NYSE"
        
        # Clean symbol (remove .NS, .BO)
        clean_sym = symbol.split('.')[0]
        
        url = f"https://www.google.com/finance/quote/{clean_sym}:{exch}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200: return None
        
        # Find price in data-last-price attribute
        match = re.search(r'data-last-price="([\d\.,]+)"', response.text)
        if match:
            return float(match.group(1).replace(',', ''))
        
        # Fallback to visual class
        price_match = re.search(r'class="YMlS7e">[^<]*?([\d,]+\.\d+)', response.text)
        if price_match:
            return float(price_match.group(1).replace(',', ''))
            
        return None
    except:
        return None
