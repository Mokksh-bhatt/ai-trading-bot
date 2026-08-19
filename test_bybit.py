import sys
import os
from dotenv import load_dotenv

# Ensure the script can import from backend
sys.path.insert(0, os.path.abspath('.'))

load_dotenv(override=True)
BYBIT_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_SECRET = os.getenv("BYBIT_API_SECRET")

try:
    from pybit.unified_trading import HTTP
    client = HTTP(demo=True, api_key=BYBIT_KEY, api_secret=BYBIT_SECRET, max_retries=1)
    response = client.get_positions(category="linear", symbol="BTCUSDT")
    print("SUCCESS! Bybit accepted the request.")
except Exception as e:
    print(f"FAILED: {e}")
