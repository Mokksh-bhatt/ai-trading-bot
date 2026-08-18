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
    exchange.set_sandbox_mode(True)
    
    # Test balance
    balance = exchange.fetch_balance()
    usdt_balance = balance.get('USDT', {}).get('free', 0)
    print(f"Bybit Testnet USDT Free Balance: {usdt_balance}")
    
    # Test creating a mock DOGE/USDT short order just to be absolutely sure permissions are right
    # Using tiny amount
    try:
        # DOGE/USDT:USDT is the CCXT bybit swap symbol
        symbol = 'DOGE/USDT:USDT'
        # To avoid error if user doesn't have balance, we just fetch market first
        markets = exchange.load_markets()
        market = markets[symbol]
        print(f"Verified {symbol} market exists.")
    except Exception as em:
        print(f"Market fetch error: {em}")
            
except Exception as e:
    print(f"Bybit Error: {e}")
