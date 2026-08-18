import os
import ccxt
from dotenv import load_dotenv

load_dotenv("backend/.env")
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_API_SECRET")

try:
    exchange = ccxt.binance({
        'apiKey': BINANCE_KEY,
        'secret': BINANCE_SECRET,
        'enableRateLimit': True
    })
    
    # Test balance
    balance = exchange.fetch_balance()
    usdt_balance = balance.get('USDT', {}).get('free', 0)
    print(f"Binance Spot USDT Free Balance: {usdt_balance}")
            
except Exception as e:
    print(f"Binance Error: {e}")
