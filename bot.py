import json
import time
import requests
from datetime import datetime

# Files
PORTFOLIO_FILE = 'portfolio.json'

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log_movement(portfolio, message):
    """Har single movement ko time ke sath capture karta hai"""
    timestamp = get_current_time()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry) # GitHub Actions terminal ke liye
    portfolio['logs'].append(log_entry)
    
    # Har baar log save karna taaki track rahe
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=4)

def fetch_btc_price():
    """Binance Public API se bina login kiye price lana"""
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        return None

def run_paper_trader():
    # 1. Load Portfolio
    with open(PORTFOLIO_FILE, 'r') as f:
        portfolio = json.load(f)
    
    log_movement(portfolio, "Bot Started. Fetching market data...")

    # 2. Get Price
    current_price = fetch_btc_price()
    if not current_price:
        log_movement(portfolio, "ERROR: Binance API se price fetch nahi ho paya.")
        return

    log_movement(portfolio, f"Current BTC Price: ${current_price}")
    
    # ==========================================
    # STRATEGY ENGINE (Yahan aap apne rules laga sakte hain)
    # Example: Simple Price Drop Strategy
    # Agar status WAITING hai aur price condition match hoti hai toh BUY karo
    # ==========================================
    
    # Dummy Condition: Buy if we have USDT balance
    if portfolio['status'] == "WAITING" and portfolio['balance_usdt'] > 0:
        buy_amount_usdt = portfolio['balance_usdt'] # Pura $1000 laga diya
        btc_bought = buy_amount_usdt / current_price
        
        # Portfolio Update
        portfolio['balance_usdt'] = 0.0
        portfolio['holding_btc'] = btc_bought
        portfolio['status'] = "IN_TRADE"
        
        trade_details = {
            "type": "BUY",
            "price": current_price,
            "btc_amount": btc_bought,
            "time": get_current_time()
        }
        portfolio['trade_history'].append(trade_details)
        log_movement(portfolio, f"🚀 RULE MATCHED: Executed BUY order for {btc_bought:.4f} BTC at ${current_price}")
        
    elif portfolio['status'] == "IN_TRADE" and portfolio['holding_btc'] > 0:
        # Dummy Condition: Sell logic (Example: Har haal mein sell kar do agle run mein)
        # Real scenario mein yahan aap Stop-Loss ya Take-Profit ka math lagayenge
        usdt_received = portfolio['holding_btc'] * current_price
        
        # Portfolio Update
        portfolio['balance_usdt'] = usdt_received
        portfolio['holding_btc'] = 0.0
        portfolio['status'] = "WAITING"
        
        trade_details = {
            "type": "SELL",
            "price": current_price,
            "usdt_received": usdt_received,
            "time": get_current_time()
        }
        portfolio['trade_history'].append(trade_details)
        
        # P/L Calculate karna
        profit = usdt_received - 1000 # initial balance 1000 tha
        log_movement(portfolio, f"💰 EXECUTED SELL order. Received ${usdt_received:.2f}. Total Profit/Loss: ${profit:.2f}")
    
    else:
        log_movement(portfolio, "No rules matched. Waiting for next cycle.")

    log_movement(portfolio, "Bot cycle completed.")

if __name__ == "__main__":
    run_paper_trader()
