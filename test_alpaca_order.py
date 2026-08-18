import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv

load_dotenv("backend/.env")
API_KEY = os.getenv("ALPACA_API_KEY", "")
API_SECRET = os.getenv("ALPACA_API_SECRET", "")

print(f"Key: {API_KEY}")

client = TradingClient(API_KEY, API_SECRET, paper=True)

try:
    print("Fetching open positions from Alpaca...")
    positions = client.get_all_positions()
    print(f"Found {len(positions)} open positions on Alpaca.")
    for p in positions:
        print(f" - {p.symbol}: {p.qty} shares/coins (Side: {p.side}) PnL: ${p.unrealized_pl}")
except Exception as e:
    print(f"Error fetching positions: {e}")
