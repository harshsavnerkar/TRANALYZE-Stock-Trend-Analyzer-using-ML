import json
import os

def process_symbols(market):
    raw_path = f"{market.lower()}_symbols.json"
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found")
        return

    with open(raw_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    if isinstance(data, dict):
        symbols = sorted(list(data.values()))
    elif isinstance(data, list):
        symbols = sorted(data)
    else:
        symbols = []
    
    with open(f"{market.lower()}_symbols_list.json", 'w', encoding='utf-8') as f:
        json.dump(symbols, f, indent=4)
        
    print(f"Successfully processed {len(symbols)} {market} symbols.")

if __name__ == "__main__":
    process_symbols("nse")
    process_symbols("bse")
