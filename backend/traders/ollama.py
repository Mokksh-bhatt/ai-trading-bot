import requests
import json
from backend.traders.base import Trader, TraderDecision
from backend.models import MarketSnapshot

class OllamaTrader(Trader):
    def __init__(self, model_name: str = "qwen2.5-coder:7b"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/chat"

    def decide(self, snapshot: MarketSnapshot, context: dict) -> TraderDecision:
        sys_prompt = f"""
You are a HIGH-FREQUENCY SCALPING AI. Your entire existence revolves around rapid-fire execution for the next 20 to 30 seconds.
Your objective: Take SUPER SHORT WINS again and again. You DO NOT care about the macro session trend. You ONLY care about what the price will do in the next 30 seconds to make a few bucks!
If you just sold, you must immediately look for the next tiny dip to BUY again. 
If you make a loss, regain it instantly by entering a new rapid scalp. Take profit at the slightest upward or downward movement.

Do not be overly cautious. Execute BUYS and SELLS continuously. We are SCALPING. Let's rack up the trade count and print micro-profits win after win!

Market Snapshot:
Symbol: {snapshot.symbol}
Asset Class: {snapshot.asset_class}
Price: {snapshot.price}
Volume: {snapshot.volume}

Context:
{json.dumps(context)}

CRITICAL TECHNICAL ANALYSIS ENTRY RULES:
Your Context now contains a "TA" object with RSI_14, SMA_9, and SMA_20.
- NEVER BUY if RSI_14 is > 65. The asset is OVERBOUGHT and due for a correction. Wait for a dip.
- STRONG BUY if RSI_14 is < 35. The asset is OVERSOLD.
- ONLY BUY if SMA_9 > SMA_20 (short-term momentum is bullish). Do not catch falling knives!

LONG-TERM LEARNED RULES:
You have compiled the following core truths from your long-term historical performance:
{json.dumps(context.get('long_term_lessons', []))}
YOU MUST OBEY THESE TRUTHS UNCONDITIONALLY.

Review your past trades provided in the context (if any). Learn immediately from your mistakes (negative PnL) and reinforce your wins (positive PnL) to continuously evolve your strategy for maximum profit extraction.

Expected JSON format:
{{
    "bias": "bullish" | "bearish" | "neutral",
    "confidence": 0.0-1.0,
    "reasoning": "Explain why this bias is correct based on the TA rules and current context",
    "timeframe_tag": "string (e.g., scalp, swing)"
}}
"""
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": f"Provide your market bias for {snapshot.symbol} at current price {snapshot.price:.2f}"}
            ],
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=180)
            response.raise_for_status()
            result_json = response.json().get("message", {}).get("content", "{}")
            decision = json.loads(result_json)
            
            # Map bias to an actionable bias object
            bias = decision.get("bias", "neutral").lower()
            
            return {
                "action": bias, # we overload 'action' to pass the bias back to the fast loop
                "size_pct": float(decision.get("size_pct", 10.0)),
                "confidence": float(decision.get("confidence", 0.0)),
                "reasoning": decision.get("reasoning", "No reasoning provided"),
                "timeframe_tag": decision.get("timeframe_tag", "intraday")
            }
        except Exception as e:
            return {
                "action": "neutral",
                "size_pct": 0.0,
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
                "timeframe_tag": "error"
            }
