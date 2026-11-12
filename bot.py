import json
import time
import requests
from datetime import datetime
import os

PORTFOLIO_FILE = 'trading.json'

def get_current_time():
    """Current time return karta hai"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def fetch_binance_public_price(symbol="BTCUSDT"):
    """Bina kisi API key ke Binance se current price fetch karna"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def log_and_save(portfolio, message):
    """Logs update karke json file mein save karta hai"""
    timestamp = get_current_time()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    # Naye log ko list ke shuru mein add karein taaki latest hamesha upar rahe
    portfolio['logs'].insert(0, log_entry)
    
    # File save karna
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=4)

def run_trading_cycle():
    # 1. Purana data load karna (Agar file exist nahi karti toh error dega)
    if not os.path.exists(PORTFOLIO_FILE):
        print(f"Error: {PORTFOLIO_FILE} nahi mili!")
        return

    with open(PORTFOLIO_FILE, 'r') as f:
        portfolio = json.load(f)

    log_and_save(portfolio, "Cycle Started. Fetching market data...")

    # 2. Binance API call
    current_price = fetch_binance_public_price()
    if not current_price:
        log_and_save(portfolio, "Binance Public API se price nahi mila. Skipping this minute.")
        return

    log_and_save(portfolio, f"Current BTC Price: ${current_price}")
    
    # 3. YAHAN AAPKI MAIN STRATEGY AAYEGI (Example Logic Below)
    
    # Condition: Agar $1000 balance hai aur coin sasta hua hai (sirf example)
    if portfolio['status'] == "WAITING" and portfolio['balance_usdt'] > 0:
        # Pura balance laga diya
        buy_amount = portfolio['balance_usdt']
        btc_bought = buy_amount / current_price
        
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
        log_and_save(portfolio, f"🚀 STRATEGY TRIGGERED: BUY {btc_bought:.5f} BTC at ${current_price}")

    # Condition: Agar coin hold kiya hai, toh usko sell karo
    elif portfolio['status'] == "IN_TRADE" and portfolio['holding_btc'] > 0:
        usdt_received = portfolio['holding_btc'] * current_price
        
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
        
        profit = usdt_received - 1000.0
        log_and_save(portfolio, f"💰 STRATEGY TRIGGERED: SELL Executed. Received ${usdt_received:.2f}. Total P/L: ${profit:.2f}")
    
    else:
        log_and_save(portfolio, "No strategy rules matched. Waiting...")

# GitHub Actions ko 5 min chalaane ke liye loop
if __name__ == "__main__":
    for i in range(5):
        print(f"\n--- Minute {i+1} Check ---")
        run_trading_cycle()
        
        # Aakhri (5th) baar sleep ki zaroorat nahi hai
        if i < 4:
            time.sleep(60)
