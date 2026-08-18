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
from dotenv import load_dotenv
load_dotenv(override=True)
from datetime import datetime, timezone

import random

ALL_SYMBOLS = [
    ("BTC/USDT", "crypto"), ("ETH/USDT", "crypto"), ("SOL/USDT", "crypto"), ("DOGE/USDT", "crypto"),
    ("XRP/USDT", "crypto"), ("ADA/USDT", "crypto"), ("AVAX/USDT", "crypto"), ("MSTR", "stock")
]

# The AI dynamically picks assets, but user requested DOGE and MSTR specifically
SYMBOLS = [
    ("DOGE/USDT", "crypto"),
    ("MSTR", "stock"),
    ("BTC/USDT", "crypto")
]

from backend.traders.ollama import OllamaTrader

heuristic = OllamaTrader()

import json
import os

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
    return {s[0]: {"bias": "neutral", "reasoning": "Initializing..."} for s in SYMBOLS}

def save_bias_cache(cache):
    with open(BIAS_CACHE_FILE, "w") as f:
        json.dump(cache, f)

AI_MACRO_BIAS = load_bias_cache()
API_ERRORS = {}

async def macro_analysis_loop():
    print("[INIT] Macro AI Analysis Loop Started (60s tick)", flush=True)
    cycle_count = 0
    while True:
        print("--- [MACRO CYCLE START] AI Analyzing Market Trends ---", flush=True)
        for symbol, asset_class in SYMBOLS:
            try:
                # Check if cache is fresh enough to skip (e.g., if we just booted and cache is < 5 mins old)
                # But since this loop sleeps 60s anyway, we just run it and update the cache.
                snapshot = await asyncio.to_thread(fetch_market_snapshot, symbol, asset_class)
                from backend.db import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                
                base_context = snapshot.context or {}
                long_term_rules = get_learned_rules()
                base_context.update({"avg_volume": snapshot.volume * 0.95, "recent_trend": "active", "long_term_lessons": long_term_rules})
                
                cursor.execute("SELECT symbol, realized_pnl, pnl_pct FROM trades WHERE model_name = 'HeuristicTrader' AND status = 'closed' ORDER BY id DESC LIMIT 3")
                o_past = [dict(r) for r in cursor.fetchall()]
                
                cursor.execute("SELECT entry_price, direction FROM trades WHERE model_name = 'HeuristicTrader' AND symbol = ? AND status = 'open'", (symbol,))
                o_open = cursor.fetchone()
                current_pos = None
                if o_open:
                    entry_price = o_open["entry_price"]
                    direction = o_open["direction"]
                    if direction == "long":
                        live_pnl_pct = ((snapshot.price - entry_price) / entry_price) * 100
                    else:
                        live_pnl_pct = ((entry_price - snapshot.price) / entry_price) * 100
                    current_pos = {"direction": direction, "entry_price": entry_price, "current_price": snapshot.price, "live_pnl_pct": round(live_pnl_pct, 4)}
                
                o_context = {**base_context, "past_trades": o_past, "current_position": current_pos}
                if symbol in API_ERRORS:
                    o_context["recent_api_error_from_exchange"] = API_ERRORS[symbol]
                    
                o_decision = await asyncio.to_thread(heuristic.decide, snapshot, o_context)
                bias = str(o_decision.get("action", "neutral")).lower()
                reasoning = o_decision.get("reasoning", "No reasoning")
                
                # Map various AI outputs to strict macro signals
                if bias in ["buy", "bullish"]: clean_bias = "bullish"
                elif bias in ["sell", "bearish"]: clean_bias = "bearish"
                else: clean_bias = "neutral"
                
                AI_MACRO_BIAS[symbol] = {
                    "bias": clean_bias,
                    "reasoning": reasoning,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                save_bias_cache(AI_MACRO_BIAS)
                
                print(f"[MACRO AI] {symbol} Bias set to: {clean_bias.upper()} | Reason: {reasoning}", flush=True)
                
                conn.close()
            except Exception as e:
                print(f"[MACRO ERROR] {symbol}: {e}", flush=True)
                
        cycle_count += 1
        if cycle_count % 10 == 0:
            asyncio.create_task(asyncio.to_thread(generate_long_term_memory, "qwen2.5-coder:7b"))
            
        await asyncio.sleep(60)

async def fast_execution_loop():
    print("[INIT] High-Frequency Grid Execution Loop Started (2s tick)", flush=True)
    
    # Dictionary to track when a symbol is allowed to trade again after an error
    import time
    error_cooldowns = {}
    
    while True:
        for symbol, asset_class in SYMBOLS:
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
                
                cursor.execute("SELECT entry_price, direction FROM trades WHERE model_name = 'HeuristicTrader' AND symbol = ? AND status = 'open'", (symbol,))
                o_open = cursor.fetchone()
                
                if o_open:
                    entry_price = o_open["entry_price"]
                    direction = o_open["direction"]
                    
                    if direction == "long":
                        live_pnl_pct = ((price - entry_price) / entry_price) * 100
                    else:
                        live_pnl_pct = ((entry_price - price) / entry_price) * 100
                    
                    # Hyper-tight auto-TP/SL
                    if live_pnl_pct > 0.03 or live_pnl_pct < -0.10:
                        reason = f"Grid Execution Auto-Exit ({direction.upper()}) at {live_pnl_pct:.4f}%"
                        decision = {"action": "close", "confidence": 1.0, "reasoning": reason, "timeframe_tag": "hft"}
                        await asyncio.to_thread(execute_paper_trade, "HeuristicTrader", decision, lite_snap)
                else:
                    # Flat. Check AI bias.
                    macro_state = AI_MACRO_BIAS.get(symbol, {})
                    bias = macro_state.get("bias", "neutral")
                    
                    if bias == "bullish":
                        decision = {"action": "buy", "confidence": 0.9, "reasoning": "AI Bias Bullish Trigger", "timeframe_tag": "hft"}
                    elif bias == "bearish":
                        decision = {"action": "sell", "confidence": 0.9, "reasoning": "AI Bias Bearish Trigger", "timeframe_tag": "hft"}
                    else:
                        decision = {"action": "hold", "confidence": 0.0, "reasoning": "AI Bias Neutral", "timeframe_tag": "hft"}
                        
                    err = await asyncio.to_thread(execute_paper_trade, "HeuristicTrader", decision, lite_snap)
                    if err:
                        API_ERRORS[symbol] = err
                        error_cooldowns[symbol] = current_time + 60.0 # 60 second cooldown on error
                
                conn.close()
            except Exception as e:
                print(f"[FAST LOOP ERROR] {e}")
        await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task1 = asyncio.create_task(macro_analysis_loop())
    task2 = asyncio.create_task(fast_execution_loop())
    yield
    task1.cancel()
    task2.cancel()

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
