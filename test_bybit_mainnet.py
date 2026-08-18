import os
import ccxt
from dotenv import load_dotenv

load_dotenv("backend/.env")
BYBIT_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_SECRET = os.getenv("BYBIT_API_SECRET")

try:
    exchange = ccxt.bybit({
        'apiKey': BYBIT_KEY,
        'secret': BYBIT_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    # exchange.set_sandbox_mode(True) # Testing mainnet!
    
    # Test balance
    balance = exchange.fetch_balance()
    usdt_balance = balance.get('USDT', {}).get('free', 0)
    print(f"Bybit Mainnet USDT Free Balance: {usdt_balance}")
            
except Exception as e:
    print(f"Bybit Error: {e}")
