import os
import json
import time
from datetime import datetime
import ccxt

PORTFOLIO_FILE = 'trading.json'
STOP_LOSS_PCT = 0.010  
TAKE_PROFIT_PCT = 0.015  

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log_and_save(portfolio, message):
    timestamp = get_current_time()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    portfolio['logs'].insert(0, log_entry)
    if len(portfolio['logs']) > 50:
        portfolio['logs'] = portfolio['logs'][:50]
        
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=4)

def check_and_execute_trade(portfolio, current_price):
    status = portfolio['status']
    
    # WAITING -> BUY
    if status == "WAITING" and portfolio['balance_usdt'] > 0:
        buy_amount = portfolio['balance_usdt']
        btc_bought = buy_amount / current_price
        
        portfolio['balance_usdt'] = 0.0
        portfolio['holding_btc'] = btc_bought
        portfolio['entry_price'] = current_price
        portfolio['status'] = "IN_TRADE"
        
        target_price = current_price * (1 + TAKE_PROFIT_PCT)
        stop_price = current_price * (1 - STOP_LOSS_PCT)
        
        portfolio['trade_history'].append({
            "type": "BUY",
            "entry_price": current_price,
            "btc_amount": btc_bought,
            "target_tp": target_price,
            "target_sl": stop_price,
            "time": get_current_time()
        })
        
        log_and_save(portfolio, f"🎯 EXECUTED BUY: {btc_bought:.5f} BTC at ${current_price:.2f}")
        log_and_save(portfolio, f"🔒 SL set at ${stop_price:.2f} | 🟢 TP set at ${target_price:.2f}")

    # IN_TRADE -> SELL
    elif status == "IN_TRADE" and portfolio['holding_btc'] > 0:
        entry_price = portfolio.get('entry_price', current_price)
        
        if current_price <= (entry_price * (1 - STOP_LOSS_PCT)):
            sell_amount = portfolio['holding_btc'] * current_price
            loss = 25.0 - sell_amount 
            
            portfolio['balance_usdt'] = sell_amount
            portfolio['holding_btc'] = 0.0
            portfolio['status'] = "WAITING"
            
            log_and_save(portfolio, f"🛑 STOP LOSS HIT at ${current_price:.2f}. Executed Sell. Loss: ${loss:.2f}")
            
        elif current_price >= (entry_price * (1 + TAKE_PROFIT_PCT)):
            sell_amount = portfolio['holding_btc'] * current_price
            profit = sell_amount - 25.0
            
            portfolio['balance_usdt'] = sell_amount
            portfolio['holding_btc'] = 0.0
            portfolio['status'] = "WAITING"
            
            log_and_save(portfolio, f"🎉 TAKE PROFIT HIT at ${current_price:.2f}. Executed Sell. Profit: ${profit:.2f}")
            
        else:
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            log_and_save(portfolio, f"👀 Holding Position. Current P/L: {pnl_percent:.2f}% (Price: ${current_price:.2f})")

def run_cycle():
    if not os.path.exists(PORTFOLIO_FILE):
        print(f"Error: {PORTFOLIO_FILE} missing.")
        return

    with open(PORTFOLIO_FILE, 'r') as f:
        portfolio = json.load(f)

    log_and_save(portfolio, "-----------------------------------")
    
    # 1. Binance se secure connection banana (using GitHub Secrets keys)
    api_key = os.environ.get('BINANCE_API_KEY')
    api_secret = os.environ.get('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        log_and_save(portfolio, "Error: API Keys GitHub Secrets mein nahi mili!")
        return

    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

    # 2. Market price fetch karna API ke through
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        log_and_save(portfolio, f"Live Price Fetch (CCXT): ${current_price:.2f}")
        check_and_execute_trade(portfolio, current_price)
    except Exception as e:
        log_and_save(portfolio, f"Exchange Error: {str(e)}")

if __name__ == "__main__":
    for i in range(5):
        print(f"\n[Minute {i+1}] Processing...")
        run_cycle()
        if i < 4:
            time.sleep(60)
