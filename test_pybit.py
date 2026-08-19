import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv('.env')
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

try:
    session = HTTP(
        testnet=True,
        api_key=api_key,
        api_secret=api_secret,
    )
    print(session.get_wallet_balance(accountType="UNIFIED"))
except Exception as e:
    print(f"Pybit Error: {e}")
