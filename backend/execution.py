import os
from datetime import datetime, timezone
import json
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from pybit.unified_trading import HTTP

from backend.models import MarketSnapshot, TradeRecord
from backend.traders.base import TraderDecision
from backend.db import get_db_connection, get_supabase

load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY", "")
API_SECRET = os.getenv("ALPACA_API_SECRET", "")

BYBIT_KEY = os.getenv("BYBIT_API_KEY", "")
BYBIT_SECRET = os.getenv("BYBIT_API_SECRET", "")

def get_alpaca_client():
    if not API_KEY or not API_SECRET or API_KEY == "YOUR_ALPACA_API_KEY_HERE":
        return None
    # PAPER TRADING ACCOUNT
    return TradingClient(API_KEY, API_SECRET, paper=True)

def get_bybit_client():
    if not BYBIT_KEY or not BYBIT_SECRET:
        return None
    # We detected the user is using Bybit Demo Trading!
    return HTTP(
        demo=True,
        api_key=BYBIT_KEY,
        api_secret=BYBIT_SECRET,
        recv_window=60000
    )

def execute_paper_trade(
    model_name: str, 
    decision: TraderDecision, 
    snapshot: MarketSnapshot
) -> str | None:
    alpaca_client = get_alpaca_client()
    bybit_client = get_bybit_client()

    alpaca_symbol = snapshot.symbol.replace("USDT", "USD") if snapshot.asset_class == "crypto" else snapshot.symbol
    bybit_symbol = f"{snapshot.symbol.replace('/USDT', '')}/USDT:USDT" if snapshot.asset_class == "crypto" else snapshot.symbol

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check for open position locally
    cursor.execute(
        "SELECT * FROM trades WHERE model_name = ? AND symbol = ? AND status = 'open'",
        (model_name, snapshot.symbol)
    )
    open_trade = cursor.fetchone()
    
    # Mark to market if position is open
    if open_trade:
        direction = open_trade["direction"]
        if direction == "long":
            unrealized_pnl = (snapshot.price - open_trade["entry_price"]) * open_trade["quantity"]
            pnl_pct = ((snapshot.price - open_trade["entry_price"]) / open_trade["entry_price"]) * 100
        else:
            unrealized_pnl = (open_trade["entry_price"] - snapshot.price) * open_trade["quantity"]
            pnl_pct = ((open_trade["entry_price"] - snapshot.price) / open_trade["entry_price"]) * 100
            
        cursor.execute(
            "UPDATE trades SET unrealized_pnl = ?, pnl_pct = ? WHERE id = ?",
            (unrealized_pnl, pnl_pct, open_trade["id"])
        )
        conn.commit()

    if decision["action"] == "hold":
        print(f"[{model_name}] HOLD {snapshot.symbol} (Confidence: {decision.get('confidence', 0):.2f})", flush=True)
        conn.close()
        return
        
    if decision["action"] in ["buy", "sell"] and not open_trade:
        direction = "long" if decision["action"] == "buy" else "short"
        side = OrderSide.BUY if direction == "long" else OrderSide.SELL
        
        entry_price_val = snapshot.price
        quantity_val = 1000.0 / snapshot.price
        
        # STOCK EXECUTION (ALPACA)
        if snapshot.asset_class == "stock":
            if alpaca_client:
                try:
                    market_order_data = MarketOrderRequest(
                        symbol=alpaca_symbol,
                        notional=1000,
                        side=side,
                        time_in_force=TimeInForce.DAY
                    )
                    order = alpaca_client.submit_order(order_data=market_order_data)
                    print(f"[{model_name}] [ALPACA {side.name}] Sent Live Paper Order for {alpaca_symbol}!", flush=True)
                    
                    import time
                    from alpaca.trading.enums import OrderStatus
                    for _ in range(6):
                        time.sleep(0.5)
                        order_status = alpaca_client.get_order_by_id(order.id)
                        if order_status.status == OrderStatus.FILLED:
                            entry_price_val = float(order_status.filled_avg_price)
                            quantity_val = float(order_status.filled_qty)
                            break
                except Exception as e:
                    print(f"[ALPACA ERROR] {str(e)}", flush=True)
                    return # Exit without simulating
            else:
                print(f"[WARNING] No Alpaca Keys. Cannot execute {side.name} for {snapshot.symbol}.", flush=True)
                return # Exit without simulating
        
        # CRYPTO EXECUTION (BYBIT)
        elif snapshot.asset_class == "crypto":
            if bybit_client:
                try:
                    pybit_side = "Buy" if direction == "long" else "Sell"
                    print(f"[{model_name}] [BYBIT {pybit_side.upper()}] Sending Demo Order for {snapshot.symbol}!", flush=True)
                    
                    pybit_symbol = snapshot.symbol.replace("/", "")
                    # Fetch instrument info for precision
                    market_info = bybit_client.get_instruments_info(category="linear", symbol=pybit_symbol)
                    qty_step = float(market_info['result']['list'][0]['lotSizeFilter']['qtyStep'])
                    
                    # Round down to nearest qty_step
                    qty_to_trade = (quantity_val // qty_step) * qty_step
                    
                    import time
                    original_time = time.time
                    try:
                        time.time = lambda: original_time() - 2.0
                        order = bybit_client.place_order(
                            category="linear",
                            symbol=pybit_symbol,
                            side=pybit_side,
                            orderType="Market",
                            qty=str(qty_to_trade)
                        )
                    finally:
                        time.time = original_time
                    
                    # Simulated execution metrics since Demo Market Orders fill instantly
                    entry_price_val = snapshot.price
                    quantity_val = float(qty_to_trade)
                        
                except Exception as e:
                    error_msg = f"[BYBIT ERROR] {str(e)}"
                    print(error_msg, flush=True)
                    return error_msg
            else:
                error_msg = f"[WARNING] No Bybit Keys. Cannot execute {side.name} for {snapshot.symbol}."
                print(error_msg, flush=True)
                return error_msg


        entry_time = datetime.now(timezone.utc).isoformat()
        simulated_fees = (entry_price_val * quantity_val) * 0.0001
        
        cursor.execute("""
        INSERT INTO trades (model_name, strategy_tag, asset_class, symbol, status, direction, quantity, entry_price, entry_time, unrealized_pnl, realized_pnl, simulated_fees, reasoning_text, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_name,
            decision.get("timeframe_tag", "intraday"),
            snapshot.asset_class,
            snapshot.symbol,
            "open",
            direction,
            quantity_val,
            entry_price_val,
            entry_time,
            0.0,
            0.0,
            simulated_fees,
            decision.get("reasoning", "No reasoning"),
            float(decision.get("confidence", 0.0))
        ))
        conn.commit()
        print(f"[{model_name}] [OPEN {direction.upper()}] {snapshot.symbol} @ ${entry_price_val:.4f} | Qty: {quantity_val:.4f} | Conf: {decision.get('confidence', 0):.2f}", flush=True)

    elif decision["action"] == "close" or (decision["action"] in ["buy", "sell"] and open_trade):
        if open_trade:
            exit_price_val = snapshot.price
            direction = open_trade["direction"]
            entry_price = float(open_trade["entry_price"])
            quantity = float(open_trade["quantity"])
            
            # STOCK EXECUTION (ALPACA)
            if snapshot.asset_class == "stock":
                if alpaca_client:
                    try:
                        order = alpaca_client.close_position(symbol_or_asset_id=alpaca_symbol)
                        print(f"[{model_name}] [ALPACA CLOSE] Closed Live Position for {alpaca_symbol}!", flush=True)
                        
                        import time
                        from alpaca.trading.enums import OrderStatus
                        for _ in range(6):
                            time.sleep(0.5)
                            order_status = alpaca_client.get_order_by_id(order.id)
                            if order_status.status == OrderStatus.FILLED:
                                exit_price_val = float(order_status.filled_avg_price)
                                break
                                
                    except Exception as e:
                        print(f"[ALPACA ERROR] {str(e)}", flush=True)
                        return # Exit without simulating
                else:
                    print(f"[WARNING] No Alpaca Keys. Cannot Close {snapshot.symbol}.", flush=True)
                    return # Exit without simulating

            # CRYPTO EXECUTION (BYBIT)
            elif snapshot.asset_class == "crypto":
                if bybit_client:
                    try:
                        pybit_side = "Sell" if direction == "long" else "Buy"
                        print(f"[{model_name}] [BYBIT {pybit_side.upper()}] Closing Demo Position for {snapshot.symbol}!", flush=True)
                        
                        pybit_symbol = snapshot.symbol.replace("/", "")
                        # Fetch instrument info for precision
                        market_info = bybit_client.get_instruments_info(category="linear", symbol=pybit_symbol)
                        qty_step = float(market_info['result']['list'][0]['lotSizeFilter']['qtyStep'])
                        
                        qty_to_close = (quantity // qty_step) * qty_step
                        
                        import time
                        original_time = time.time
                        try:
                            time.time = lambda: original_time() - 2.0
                            order = bybit_client.place_order(
                                category="linear",
                                symbol=pybit_symbol,
                                side=pybit_side,
                                orderType="Market",
                                qty=str(qty_to_close),
                                reduceOnly=True
                            )
                        finally:
                            time.time = original_time
                        
                        exit_price_val = snapshot.price
                            
                    except Exception as e:
                        print(f"[BYBIT ERROR] {str(e)}", flush=True)
                        return # Exit without simulating
                else:
                    print(f"[WARNING] No Bybit Keys. Cannot Close {snapshot.symbol}.", flush=True)
                    return # Exit without simulating
            
            exit_fee = (exit_price_val * quantity) * 0.0001
            total_fees = float(open_trade["simulated_fees"]) + exit_fee
            
            if direction == "long":
                realized_pnl = ((exit_price_val - entry_price) * quantity) - total_fees
                pnl_pct = ((exit_price_val - entry_price) / entry_price) * 100
            else:
                realized_pnl = ((entry_price - exit_price_val) * quantity) - total_fees
                pnl_pct = ((entry_price - exit_price_val) / entry_price) * 100
            
            exit_time = datetime.now(timezone.utc).isoformat()
            updated_reason = f"{open_trade['reasoning_text']} \n\n[EXIT SIGNAL]: {decision.get('reasoning', '')}"
            
            cursor.execute("""
            UPDATE trades 
            SET status = 'closed', exit_price = ?, exit_time = ?, realized_pnl = ?, pnl_pct = ?, simulated_fees = ?, reasoning_text = ?
            WHERE id = ?
            """, (exit_price_val, exit_time, realized_pnl, pnl_pct, total_fees, updated_reason, open_trade["id"]))
            conn.commit()
            print(f"[{model_name}] [CLOSED {direction.upper()}] {snapshot.symbol} @ ${exit_price_val:.4f} | Realized PnL: ${realized_pnl:.2f}", flush=True)
        else:
            print(f"[{model_name}] [SKIP CLOSE] No open position for {snapshot.symbol} to close.", flush=True)
            
    conn.close()
