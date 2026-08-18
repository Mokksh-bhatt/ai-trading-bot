import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.execution import execute_paper_trade
from backend.models import MarketSnapshot
from backend.db import get_db_connection, init_local_db

def test_paper_trading_execution():
    # 1. Initialize DB to clean slate
    init_local_db()
    
    model = "TestModel"
    symbol = "TEST/USDT"
    
    # 2. Simulate BUY
    buy_snapshot = MarketSnapshot(symbol=symbol, asset_class="crypto", price=100.0, volume=1000, timestamp="2026-08-17T00:00:00Z")
    buy_decision = {"action": "buy", "confidence": 0.9, "reasoning": "Looks good", "timeframe_tag": "intraday"}
    
    execute_paper_trade(model, buy_decision, buy_snapshot) # type: ignore
    
    conn = get_db_connection()
    trade = conn.execute("SELECT * FROM trades WHERE symbol = ?", (symbol,)).fetchone()
    assert trade is not None, "Trade was not recorded"
    assert trade["status"] == "open", "Trade status should be 'open'"
    assert trade["entry_price"] == 100.0
    # $10,000 / $100 = 100 qty
    assert trade["quantity"] == 100.0
    # Fees = $10,000 * 0.1% = $10
    assert trade["simulated_fees"] == 10.0
    
    # 3. Simulate Tick (Unrealized PnL)
    tick_snapshot = MarketSnapshot(symbol=symbol, asset_class="crypto", price=110.0, volume=1000, timestamp="2026-08-17T00:00:10Z")
    hold_decision = {"action": "hold", "confidence": 0.5, "reasoning": "Holding", "timeframe_tag": "intraday"}
    
    execute_paper_trade(model, hold_decision, tick_snapshot) # type: ignore
    
    trade = conn.execute("SELECT * FROM trades WHERE symbol = ?", (symbol,)).fetchone()
    assert trade["unrealized_pnl"] == (110.0 - 100.0) * 100.0 # 1000.0
    
    # 4. Simulate SELL (Realized PnL)
    sell_snapshot = MarketSnapshot(symbol=symbol, asset_class="crypto", price=120.0, volume=1000, timestamp="2026-08-17T00:00:20Z")
    sell_decision = {"action": "sell", "confidence": 0.8, "reasoning": "Taking profits", "timeframe_tag": "intraday"}
    
    execute_paper_trade(model, sell_decision, sell_snapshot) # type: ignore
    
    trade = conn.execute("SELECT * FROM trades WHERE symbol = ?", (symbol,)).fetchone()
    assert trade["status"] == "closed"
    assert trade["exit_price"] == 120.0
    
    # Entry fee: $10. Exit fee: 120 * 100 * 0.001 = $12. Total = $22
    assert trade["simulated_fees"] == 22.0
    
    # Gross PnL: (120 - 100) * 100 = $2000
    # Net Realized PnL: 2000 - 22 = $1978
    assert trade["realized_pnl"] == 1978.0
    
    print("All paper trading execution tests passed!")
    conn.close()

if __name__ == "__main__":
    test_paper_trading_execution()
