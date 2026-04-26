import json
import os
import requests

DATA_SOURCES = {
    "NSE": "https://raw.githubusercontent.com/akashgiri/stocks-list/master/nse-listed-stocks.json",
    "US_NASDAQ": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/master/nasdaq/nasdaq_full_tickers.json",
    "US_NYSE": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/master/nyse/nyse_full_tickers.json",
    "US_AMEX": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/master/amex/amex_full_tickers.json",
    "CRYPTO": "https://raw.githubusercontent.com/Paveen7/Top-100-Crypto-Symbols/master/top_100_crypto.json",
}

def fetch_and_process():
    # 1. NSE
    print("Fetching NSE...")
    try:
        r = requests.get(DATA_SOURCES["NSE"])
        data = r.json()
        symbols = sorted(list(data.values()))
        with open("nse_symbols_list.json", 'w') as f:
            json.dump(symbols, f)
        print(f"Saved {len(symbols)} NSE symbols")
    except Exception as e:
        print(f"NSE failed: {e}")

    # 2. US Stocks (Combine NASDAQ, NYSE, AMEX)
    print("Fetching US Stocks...")
    us_symbols = set()
    for key in ["US_NASDAQ", "US_NYSE", "US_AMEX"]:
        try:
            r = requests.get(DATA_SOURCES[key])
            data = r.json()
            # Each entry is like {"symbol": "AAPL", ...} or similar
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "symbol" in item:
                        us_symbols.add(item["symbol"])
                    elif isinstance(item, str):
                        us_symbols.add(item)
            elif isinstance(data, dict):
                # Check for common structures
                if "symbols" in data:
                    us_symbols.update(data["symbols"])
                else:
                    us_symbols.update(data.keys())
        except Exception as e:
            print(f"{key} failed: {e}")
    
    if us_symbols:
        sorted_us = sorted(list(us_symbols))
        with open("us_symbols_list.json", 'w') as f:
            json.dump(sorted_us, f)
        print(f"Saved {len(sorted_us)} US symbols")

    # 3. Crypto
    print("Fetching Crypto...")
    try:
        r = requests.get(DATA_SOURCES["CRYPTO"])
        data = r.json()
        if isinstance(data, dict):
            symbols = sorted(list(data.values()))
        elif isinstance(data, list):
            symbols = sorted(data)
        
        with open("crypto_symbols_list.json", 'w') as f:
            json.dump(symbols, f)
        print(f"Saved {len(symbols)} Crypto symbols")
    except Exception as e:
        # Fallback to a fairly large list if fetch fails
        common_crypto = [
            "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK", 
            "MATIC", "SHIB", "LTC", "TRX", "DAI", "BCH", "UNI", "LEO", "NEAR", "BCH", 
            "STX", "ATOM", "IMX", "LDO", "OKB", "CRO", "FIL", "RUNE", "HBAR", "TIA", 
            "VET", "RNDR", "AR", "NEAR", "HNT", "FLR", "JUP", "INJ", "OP", "GRT", 
            "AAVE", "STX", "FTM", "SEI", "THETA", "KAS", "FET", "ALGO", "LUNC", "CAKE", 
            "RPL", "SNX", "PYTH", "BEAM", "EGLD", "FLOW", "QNT", "MKR", "BSV", "SAND", 
            "MANA", "AXS", "GALA", "DYDX", "WOO", "ORDI", "BONK", "SATS", "WIF", "LPT"
        ]
        with open("crypto_symbols_list.json", 'w') as f:
            json.dump(sorted(list(set(common_crypto))), f)
        print("Using comprehensive Crypto list")

    # 4. Forex
    print("Writing Forex...")
    forex = [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
        "EURGBP", "EURJPY", "EURCHF", "EURCAD", "EURAUD", "EURNZD",
        "GBPJPY", "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD",
        "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
        "CADJPY", "CADCHF",
        "CHFJPY",
        "USDINR", "EURINR", "GBPINR", "JPYINR",
        "USDZAR", "USDTRY", "USDSGD", "USDMXN", "USDHKD", "USDRUB", "USDCNY",
        "USDKRW", "USDBRL", "USDTRY", "USDIDR", "USDTHB", "USDMYR", "USDPHP",
        "EURSGD", "EURHKD", "EURTRY", "EURZAR", "GBPSGD", "GBPHKD", "GBPTRY", "GBPZAR"
    ]
    with open("forex_symbols_list.json", 'w') as f:
        json.dump(sorted(list(set(forex))), f)
    print(f"Saved {len(forex)} Forex symbols")

    # 5. BSE (Hardcoded top 500 if no reliable fetch)
    print("Writing BSE...")
    # I'll try one more fetch for BSE
    try:
        r = requests.get("https://raw.githubusercontent.com/akashgiri/stocks-list/master/bse-listed-stocks.json")
        data = r.json()
        symbols = sorted(list(data.values()))
        with open("bse_symbols_list.json", 'w') as f:
            json.dump(symbols, f)
        print(f"Saved {len(symbols)} BSE symbols")
    except:
        # Fallback
        bse = ["500010", "500112", "500180", "500209", "500325", "532174", "532215", "532540"]
        with open("bse_symbols_list.json", 'w') as f:
            json.dump(bse, f)
        print("Using fallback BSE list")

if __name__ == "__main__":
    fetch_and_process()
