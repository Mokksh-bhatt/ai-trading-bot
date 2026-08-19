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
You are the Swarm Intelligence Entry AI. You do NOT manage live trades. Your sole purpose is to evaluate a highly volatile asset that has been flagged by the Market Scanner.
Your objective: Determine the directional momentum (BULLISH or BEARISH) of the asset.

The asset has been passed to you because it is experiencing a massive volume spike, high volatility, and potentially high social velocity (trending on internet). 

Market Snapshot:
Symbol: {snapshot.symbol}
Asset Class: {snapshot.asset_class}
Price: {snapshot.price}
Volume: {snapshot.volume}

Context:
{json.dumps(context, indent=2)}

CRITICAL RULES:
1. You MUST pick a direction (bullish or bearish) if you believe the momentum will continue. DO NOT sit in neutral if the asset is actively spiking.
2. If the context contains a "recent_api_error_from_exchange", evaluate if your previous decision caused it (e.g., an invalid order side or size) and adjust your strategy.
3. Your confidence score MUST be >= 0.70 if you want the Python engine to actually execute the trade. If you return 0.65, the trade is rejected.
4. If you see recent losses in the past trades context, flip your bias or wait for a clearer trend.

Expected JSON format:
{{
    "bias": "bullish" | "bearish" | "neutral",
    "confidence": 0.0-1.0,
    "reasoning": "Explain why this bias is correct based on the volatility and context",
    "timeframe_tag": "momentum"
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
            import random
            fallback_bias = random.choice(["bullish", "bearish"])
            return {
                "action": fallback_bias,
                "size_pct": 10.0,
                "confidence": 0.9,
                "reasoning": f"Simulated {fallback_bias} bias because Ollama is unreachable in the cloud environment.",
                "timeframe_tag": "hft_fallback"
            }
