from fastapi import APIRouter, Query
from backend.db import get_db_connection
from backend.ingestion import fetch_historical_prices
from typing import List

router = APIRouter()

@router.get("/api/models")
def get_models():
    return {"models": ["HeuristicTrader", "OllamaTrader"]}

@router.get("/api/trades/{model}")
def get_trades(model: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM trades WHERE model_name = ? ORDER BY id DESC",
        (model,)
    )
    rows = cursor.fetchall()
    trades = [dict(row) for row in rows]
    conn.close()
    return {"trades": trades}

@router.get("/api/stats/{model}")
def get_stats(model: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, pnl_pct, realized_pnl, unrealized_pnl FROM trades WHERE model_name = ?",
        (model,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    trades = [dict(row) for row in rows]
    closed_trades = [t for t in trades if t.get("status") == "closed"]
    open_trades = [t for t in trades if t.get("status") == "open"]
    wins = [t for t in closed_trades if (t.get("pnl_pct") or 0) > 0]
    
    total_pnl = sum(t.get("pnl_pct") or 0 for t in closed_trades)
    total_realized = sum(t.get("realized_pnl") or 0 for t in closed_trades)
    total_unrealized = sum(t.get("unrealized_pnl") or 0 for t in open_trades)
    
    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0.0
    
    return {
        "total_trades": len(trades),
        "closed_trades": len(closed_trades),
        "win_rate_pct": win_rate,
        "cumulative_pnl_pct": total_pnl,
        "cumulative_realized_pnl": total_realized,
        "live_unrealized_pnl": total_unrealized,
        "total_pnl": total_realized + total_unrealized
    }

@router.get("/api/history")
def get_history(symbol: str = Query(...), asset_class: str = Query(...)):
    history = fetch_historical_prices(symbol, asset_class)
    return {"history": history}

@router.get("/api/macro_bias")
def get_macro_bias():
    from backend.main import AI_MACRO_BIAS
    return {"macro_bias": AI_MACRO_BIAS}

@router.post("/api/panic-sell")
def panic_sell():
    from backend.main import fetch_fast_price
    from backend.execution import execute_paper_trade
    from backend.models import MarketSnapshot
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades WHERE status = 'open'")
    open_trades = cursor.fetchall()
    
    results = []
    for trade in open_trades:
        symbol = trade["symbol"]
        asset_class = trade["asset_class"]
        model = trade["model_name"]
        
        try:
            price = fetch_fast_price(symbol, asset_class)
            snap = MarketSnapshot(symbol=symbol, price=price, asset_class=asset_class)
            decision = {
                "action": "close", 
                "confidence": 1.0, 
                "reasoning": "USER TRIGGERED PANIC SELL OFF", 
                "timeframe_tag": "manual"
            }
            err = execute_paper_trade(model, decision, snap)
            if err:
                results.append({"symbol": symbol, "status": "error", "error": err})
            else:
                results.append({"symbol": symbol, "status": "closed"})
        except Exception as e:
            results.append({"symbol": symbol, "status": "error", "error": str(e)})
            
    conn.close()
    return {"message": f"Attempted to close {len(open_trades)} trades", "results": results}
