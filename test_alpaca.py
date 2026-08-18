from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")
client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_API_SECRET"), paper=True)

try:
    req = MarketOrderRequest(symbol="AAPL", notional=1000, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
    res = client.submit_order(order_data=req)
    print("AAPL OK:", res.id)
except Exception as e:
    print("AAPL ERROR:", str(e))

try:
    req2 = MarketOrderRequest(symbol="BTC/USD", notional=1000, side=OrderSide.BUY, time_in_force=TimeInForce.GTC)
    res2 = client.submit_order(order_data=req2)
    print("BTC OK:", res2.id)
except Exception as e:
    print("BTC ERROR:", str(e))
