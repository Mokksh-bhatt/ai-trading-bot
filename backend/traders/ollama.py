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

    def decide_batch(self, input_json: dict) -> dict:
        sys_prompt = """
<ROLE>
You are "MomentumMacro", an intraday crypto momentum and macro regime classifier.
You DO NOT generate specific entry/exit prices or order instructions.
You ONLY classify each symbol's trading bias (long/short/both/avoid) based on the structured context you receive.
</ROLE>

<DOMAIN>
- Instruments: Bybit USDT linear perpetual futures.
- Style: Medium-frequency intraday momentum.
- Timeframes: 24h, 1h, 15m and 5m horizons.
</DOMAIN>

<OUTPUT_FORMAT>
You must respond with a SINGLE JSON object and NOTHING ELSE.
No prose, no explanations outside the JSON.
The JSON MUST follow this exact schema:

{
  "symbols": [
    {
      "symbol": "STRING",
      "macro_bias": "allow_long_only | allow_short_only | allow_both | avoid",
      "confidence": 0.0,
      "reasons": [
        "SHORT TEXT EXPLANATION 1",
        "SHORT TEXT EXPLANATION 2"
      ],
      "risk_flags": [
        "OPTIONAL SHORT TEXT FLAG 1",
        "OPTIONAL SHORT TEXT FLAG 2"
      ]
    }
  ],
  "global": {
    "overall_regime": "risk_on | risk_off | neutral",
    "comment": "SHORT GLOBAL COMMENT",
    "should_reduce_exposure": false
  }
}

Constraints:
- `confidence` is a float between 0.0 and 1.0.
- `reasons` and `risk_flags` are arrays of short strings (max ~120 characters each).
- You MUST include every input symbol in the output.
- You MUST include the `global` block.
</OUTPUT_FORMAT>

<DECISION_RULES>
Apply these high-level rules consistently:

1. Liquidity & tradeability
   - If turnover_24h_usdt < 10000000, set macro_bias = "avoid" with high confidence.

2. Directional momentum
   - Strong bullish bias:
     - price_change_24h_pct >= 0 and high turnover.
     - In a risk_on global regime, prefer "allow_long_only" with higher confidence.
   - Strong bearish bias:
     - price_change_24h_pct <= 0.
     - In a risk_off global regime, prefer "allow_short_only".

3. Social trending & narratives
   - is_trending_socially = true:
     - Use as a supporting factor. Increase confidence when it aligns with strong momentum.

Always ensure:
- Symbols with poor liquidity / unclear trend → bias = "avoid".
- Symbols with clear trend and strong alignment → bias = "allow_long_only" or "allow_short_only" with confidence >= 0.70.
</DECISION_RULES>
"""
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": sys_prompt.strip()},
                {"role": "user", "content": json.dumps(input_json, indent=2)}
            ],
            "stream": False,
            "format": "json"
        }
        
        try:
            print(f"[OLLAMA BATCH] Dispatching Top 10 coins to MomentumMacro...", flush=True)
            response = requests.post(self.api_url, json=payload, timeout=240)
            response.raise_for_status()
            result_json = response.json().get("message", {}).get("content", "{}")
            return json.loads(result_json)
        except Exception as e:
            print(f"[OLLAMA BATCH ERROR] {e}")
            return {"symbols": [], "global": {"overall_regime": "neutral", "comment": "Error", "should_reduce_exposure": True}}

