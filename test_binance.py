import os
import ccxt
from dotenv import load_dotenv

load_dotenv("backend/.env")
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_API_SECRET")

try:
    exchange = ccxt.binanceusdm({
        'apiKey': BINANCE_KEY,
        'secret': BINANCE_SECRET,
        'enableRateLimit': True
    })
    
    # Test balance
    balance = exchange.fetch_balance()
    usdt_balance = balance.get('USDT', {}).get('free', 0)
    print(f"Binance Futures USDT Free Balance: {usdt_balance}")
    
    # Test symbol fetch
    markets = exchange.load_markets()
    btc_market = markets.get('BTC/USDT:USDT')
    if btc_market:
        print("Found BTC/USDT:USDT linear future.")
    else:
        btc_market = markets.get('BTC/USDT')
        if btc_market:
            print("Found BTC/USDT.")
        else:
            print("Could not find BTC/USDT.")
            
except Exception as e:
    print(f"Binance Error: {e}")
