import os
from pybit.unified_trading import HTTP
from alpaca.trading.client import TradingClient
from dotenv import load_dotenv

load_dotenv('.env')

print("--- BYBIT TEST ---")
try:
    import time
    original_time = time.time
    time.time = lambda: original_time() - 2.0
    
    session = HTTP(
        demo=True,
        api_key=os.getenv('BYBIT_API_KEY'),
        api_secret=os.getenv('BYBIT_API_SECRET'),
    )
    print("Bybit Wallet:", session.get_wallet_balance(accountType="UNIFIED"))
except Exception as e:
    print(f"Bybit Error: {e}")
finally:
    time.time = original_time

print("--- ALPACA TEST ---")
try:
    alpaca = TradingClient(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), paper=True)
    print("Alpaca Account:", alpaca.get_account().status)
except Exception as e:
    print(f"Alpaca Error: {e}")
