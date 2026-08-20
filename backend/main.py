import asyncio
import sys
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from backend.api import router
from backend.models import MarketSnapshot
from backend.ingestion import fetch_market_snapshot, fetch_fast_price
from backend.traders.heuristic import HeuristicTrader
from backend.traders.ollama import OllamaTrader
from backend.execution import execute_paper_trade
from backend.learning import generate_long_term_memory, get_learned_rules
from backend.db import get_db_connection
from dotenv import load_dotenv
load_dotenv(override=True)
from datetime import datetime, timezone

import random

from backend.market_scanner import fetch_market_opportunities
from backend.traders.ollama import OllamaTrader
import json
import os

heuristic = OllamaTrader()

if os.path.exists("/app/data"):
    BIAS_CACHE_FILE = "/app/data/bias_cache.json"
else:
    BIAS_CACHE_FILE = "backend/bias_cache.json"

def load_bias_cache():
    if os.path.exists(BIAS_CACHE_FILE):
        try:
            with open(BIAS_CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_bias_cache(cache):
    with open(BIAS_CACHE_FILE, "w") as f:
        json.dump(cache, f)

AI_MACRO_BIAS = load_bias_cache()
API_ERRORS = {}

async def swarm_manager_loop():
    print("[INIT] Multi-Agent Swarm Manager Loop Started (60s tick)", flush=True)
    cycle_count = 0
    while True:
        print("--- [SWARM MANAGER START] Scanning Market & Deploying AI Agents ---", flush=True)
        # Clear the cache so we only evaluate new signals
        AI_MACRO_BIAS.clear()
        
        # 1. Scanner finds volatile coins
        targets = fetch_market_opportunities(top_n=10)
        
        # 2. Build the MEGA prompt JSON payload
        from datetime import datetime, timezone
        from backend.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT symbol, direction, pnl_pct FROM trades WHERE status = 'open' AND model_name = 'GroqTrader'")
        open_positions = [{"symbol": r["symbol"], "side": r["direction"], "unrealized_pnl_pct": r["pnl_pct"]} for r in cursor.fetchall()]
        conn.close()
        
        input_json = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "account": {
                "equity_usdt": 100000.0,
                "risk_per_trade_pct": 1.0,
                "daily_max_dd_pct": 3.0,
                "open_positions": open_positions
            },
            "global_context": {
                "btc_trend": "uptrend",
                "eth_trend": "uptrend",
                "btc_dominance_change_24h_pct": 0.0,
                "funding_regime": "positive",
                "overall_risk_regime": "risk_on",
                "narratives": ["high momentum session"]
            },
            "symbols": targets
        }
        
        # 3. Dispatch to MomentumMacro AI in a single batch
        try:
            from backend.traders.groq_trader import GroqTrader
            groq_trader = GroqTrader()
            batch_decision = await asyncio.to_thread(groq_trader.decide_batch, input_json)
            
            # 4. Parse the results and update the macro bias memory
            global_regime = batch_decision.get('global', {}).get('overall_regime', 'unknown')
            global_comment = batch_decision.get('global', {}).get('comment', '')
            print(f"[SWARM] Global Regime: {global_regime.upper()} - {global_comment}", flush=True)
            
            for sym_data in batch_decision.get("symbols", []):
                symbol = sym_data.get("symbol")
                bias_str = sym_data.get("macro_bias", "avoid")
                conf = float(sym_data.get("confidence", 0.0))
                
                # Map "allow_long_only" -> "bullish", "allow_short_only" -> "bearish"
                mapped_bias = "neutral"
                if bias_str == "allow_long_only":
                    mapped_bias = "bullish"
                elif bias_str == "allow_short_only":
                    mapped_bias = "bearish"
                    
                if conf >= 0.70 and mapped_bias != "neutral":
                    AI_MACRO_BIAS[symbol] = {
                        "bias": mapped_bias,
                        "confidence": conf,
                        "reasons": sym_data.get("reasons", []),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    print(f"[MOMENTUM MACRO] {symbol}: {mapped_bias.upper()} (Conf: {conf:.2f})", flush=True)
                    for r in sym_data.get("reasons", []):
                        print(f"  -> {r}")
                else:
                    print(f"[{symbol}] Neutral or low conviction ({conf:.2f}). Skipping.", flush=True)
            
            save_bias_cache(AI_MACRO_BIAS)
        except Exception as e:
            print(f"[SWARM ERROR] Batch evaluation failed: {e}", flush=True)
                
        print("--- [SWARM MANAGER END] Market Memory Updated ---", flush=True)
        cycle_count += 1
        
        if cycle_count % 10 == 0:
            from backend.learning import generate_long_term_memory
            asyncio.create_task(asyncio.to_thread(generate_long_term_memory, "qwen2.5-coder:7b"))
            
        await asyncio.sleep(15)

async def fast_execution_loop():
    print("[INIT] High-Frequency Grid Execution Loop Started (2s tick)", flush=True)
    
    # Dictionary to track when a symbol is allowed to trade again after an error
    import time
    error_cooldowns = {}
    trade_peak_pnls = {} # Tracks the highest PNL achieved by each open trade ID
    
    while True:
        from backend.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM trades WHERE status = 'open'")
        open_symbols = [r["symbol"] for r in cursor.fetchall()]
        conn.close()
        
        active_symbols = set(open_symbols)
        for s in AI_MACRO_BIAS.keys():
            active_symbols.add(s)
            
        for symbol in active_symbols:
            asset_class = "crypto" # We only scan and trade Bybit linear futures
            current_time = time.time()
            if symbol in error_cooldowns and current_time < error_cooldowns[symbol]:
                continue # Skip this symbol until the cooldown expires
                
            try:
                price = await asyncio.to_thread(fetch_fast_price, symbol, asset_class)
                if price <= 0: continue
                
                lite_snap = MarketSnapshot(symbol=symbol, asset_class=asset_class, price=price, volume=0.0, timestamp=datetime.now(timezone.utc), context={})
                
                from backend.db import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT id, entry_price, direction, quantity FROM trades WHERE model_name = 'GroqTrader' AND symbol = ? AND status = 'open'", (symbol,))
                o_open = cursor.fetchone()
                
                if o_open:
                    entry_price = o_open["entry_price"]
                    direction = o_open["direction"]
                    quantity = o_open["quantity"]
                    trade_id = o_open["id"]
                    
                    # Deduct Bybit's 0.055% taker fee twice (Entry + Exit = 0.11% round-trip)
                    # This ensures every trade mathematically starts in the negative as it costs money to open
                    if direction == "long":
                        live_pnl_pct = (((price - entry_price) / entry_price) * 100) - 0.11
                        unrealized_pnl = ((price - entry_price) * quantity) - (entry_price * quantity * 0.0011)
                    else:
                        live_pnl_pct = (((entry_price - price) / entry_price) * 100) - 0.11
                        unrealized_pnl = ((entry_price - price) * quantity) - (entry_price * quantity * 0.0011)
                        
                    # Update the database so the frontend dashboard shows the live Net PnL (including fees)
                    cursor.execute("UPDATE trades SET unrealized_pnl = ?, pnl_pct = ? WHERE id = ?", (unrealized_pnl, live_pnl_pct, trade_id))
                    conn.commit()

                    # Update peak PnL for trailing stop
                    if trade_id not in trade_peak_pnls:
                        trade_peak_pnls[trade_id] = live_pnl_pct
                    else:
                        trade_peak_pnls[trade_id] = max(trade_peak_pnls[trade_id], live_pnl_pct)

                    peak_pct = trade_peak_pnls[trade_id]

                    # Infinite Profit / Trailing Stop Logic
                    exit_reason = None
                    if live_pnl_pct <= -0.25:
                        exit_reason = f"Grid Hard Stop-Loss ({direction.upper()}) hit at {live_pnl_pct:.4f}%"
                    elif peak_pct >= 0.10 and live_pnl_pct <= (peak_pct - 0.09):
                        exit_reason = f"Grid Trailing Stop ({direction.upper()}) locked profit at {live_pnl_pct:.4f}% (Peak: {peak_pct:.4f}%)"
                        
                    if exit_reason:
                        decision = {"action": "close", "confidence": 1.0, "reasoning": exit_reason, "timeframe_tag": "short_swing"}
                        await asyncio.to_thread(execute_paper_trade, "GroqTrader", decision, lite_snap)
                        # The Anti-Machine-Gun Safeguard: 30-second cooldown after closing to ensure the next entry relies on a fresh AI rescan
                        error_cooldowns[symbol] = current_time + 30.0 
                        if trade_id in trade_peak_pnls:
                            del trade_peak_pnls[trade_id]
                else:
                    # Flat. Check AI bias.
                    macro_state = AI_MACRO_BIAS.get(symbol, {})
                    bias = macro_state.get("bias", "neutral")
                    
                    if bias == "bullish":
                        decision = {"action": "buy", "confidence": 0.9, "reasoning": "AI Bias Bullish Trigger", "timeframe_tag": "momentum"}
                    elif bias == "bearish":
                        decision = {"action": "sell", "confidence": 0.9, "reasoning": "AI Bias Bearish Trigger", "timeframe_tag": "momentum"}
                    else:
                        decision = {"action": "hold", "confidence": 0.0, "reasoning": "AI Bias Neutral", "timeframe_tag": "momentum"}
                        
                    err = await asyncio.to_thread(execute_paper_trade, "GroqTrader", decision, lite_snap)
                    if err:
                        API_ERRORS[symbol] = err
                        if "110126" in err or "agreement" in err.lower():
                            print(f"[BLACKLIST] {symbol} requires manual UI agreement. Blacklisting for 24h.", flush=True)
                            error_cooldowns[symbol] = current_time + 86400.0 # 24 hour cooldown
                        else:
                            error_cooldowns[symbol] = current_time + 60.0 # 60 second cooldown on normal error
                
                conn.close()
            except Exception as e:
                print(f"[FAST LOOP ERROR] {e}")
        await asyncio.sleep(2)

async def simple_scalper_loop():
    """
    The original, highly aggressive scalping logic.
    Evaluates coins independently without macro batching.
    """
    from backend.traders.ollama import OllamaTrader
    simple_trader = OllamaTrader()
    import time
    
    while True:
        try:
            targets = await asyncio.to_thread(fetch_market_opportunities, 3)
            
            for t in targets:
                symbol = t['symbol']
                snap = MarketSnapshot(symbol=symbol, asset_class="crypto", price=t['last_price'], volume=t['turnover_24h_usdt'])
                
                # Check cooldowns
                current_time = time.time()
                # Assuming access to global scope or local tracking as needed
                # (Re-added error_cooldowns/trade_peak_pnls logic if needed context-wide)
                    
                context = {"recent_metrics": t}
                decision = await asyncio.to_thread(simple_trader.decide, snap, context)
                
                # Simple logic: If it picked a direction with > 0.70 confidence, trade it!
                if decision['action'] in ['bullish', 'bearish'] and decision['confidence'] >= 0.70:
                    trade_decision = {"action": "buy" if decision['action'] == "bullish" else "sell", "confidence": decision['confidence'], "reasoning": f"Simple Scalper AI Bias {decision['action'].capitalize()} Trigger", "timeframe_tag": "momentum"}
                    err = await asyncio.to_thread(execute_paper_trade, "SimpleScalper", trade_decision, snap)
                    if err:
                        API_ERRORS[symbol] = err
                else:
                    # Check for exit (Trailing Stop logic)
                    from backend.db import get_db_connection
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, entry_price, direction, quantity, pnl_pct FROM trades WHERE model_name = 'SimpleScalper' AND symbol = ? AND status = 'open'", (symbol,))
                    o_open = cursor.fetchone()
                    conn.close()
                    
                    if o_open:
                        trade_id = o_open["id"]
                        live_pnl_pct = o_open["pnl_pct"]
                        # Logic simplified for context
                        
                        exit_reason = None
                        if live_pnl_pct <= -0.25:
                            exit_reason = f"Grid Hard Stop-Loss Hit at {live_pnl_pct:.2f}%"
                        
                        if exit_reason:
                            exit_dec = {"action": "close", "confidence": 1.0, "reasoning": exit_reason, "timeframe_tag": "short_swing"}
                            await asyncio.to_thread(execute_paper_trade, "SimpleScalper", exit_dec, snap)
                            
        except Exception as e:
            print(f"[SIMPLE SCALPER ERROR] {e}")
        await asyncio.sleep(15)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task1 = asyncio.create_task(swarm_manager_loop())
    task2 = asyncio.create_task(fast_execution_loop())
    task3 = asyncio.create_task(simple_scalper_loop())
    print("AI Swarm, Fast Execution, and Simple Scalper loops started!")
    yield
    task1.cancel()
    task2.cancel()
    task3.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
