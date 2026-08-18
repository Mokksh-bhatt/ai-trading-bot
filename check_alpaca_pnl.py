import os
from alpaca.trading.client import TradingClient
from dotenv import load_dotenv

load_dotenv("backend/.env")
API_KEY = os.getenv("ALPACA_API_KEY", "")
API_SECRET = os.getenv("ALPACA_API_SECRET", "")

client = TradingClient(API_KEY, API_SECRET, paper=True)

try:
    account = client.get_account()
    equity = float(account.equity)
    last_equity = float(account.last_equity)
    todays_pnl = equity - last_equity
    todays_pnl_pct = (todays_pnl / last_equity) * 100
    
    print(f"Alpaca Equity: ${equity:.2f}")
    print(f"Alpaca Last Equity: ${last_equity:.2f}")
    print(f"Alpaca Today's PnL: ${todays_pnl:.2f} ({todays_pnl_pct:.2f}%)")
except Exception as e:
    print(f"Error: {e}")
