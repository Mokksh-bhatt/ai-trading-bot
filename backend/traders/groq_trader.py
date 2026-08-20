import os
import requests
import json
from backend.traders.base import Trader, TraderDecision
from backend.models import MarketSnapshot

class GroqTrader(Trader):
    def __init__(self, model_name: str = "llama3-70b-8192"):
        self.model_name = model_name
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = os.getenv("GROQ_API_KEY")

    def decide(self, snapshot: MarketSnapshot, context: dict) -> TraderDecision:
        # Not used in the batch architecture, but implemented for compatibility
        return {
            "action": "neutral",
            "size_pct": 10.0,
            "confidence": 0.0,
            "reasoning": "Fallback to batch processor",
            "timeframe_tag": "momentum"
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

3. Technical Indicators (CRITICAL)
   - RSI: If RSI_14 > 70, the asset is overbought (bearish bias or avoid long). If RSI_14 < 30, it is oversold (bullish bias or avoid short).
   - MACD: Align your bias with the MACD Histogram (Bullish Cross = allow_long_only).
   - Bollinger Bands: If "Touching Upper Band", heavily penalize longs (favor short). If "Touching Lower Band", heavily penalize shorts (favor long).

4. Social trending & narratives
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
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"[GROQ BATCH] Dispatching Top 10 coins to Llama 3 70B...", flush=True)
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result_json = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(result_json)
        except Exception as e:
            print(f"[GROQ BATCH ERROR] {e}")
            return {"symbols": [], "global": {"overall_regime": "neutral", "comment": "Error", "should_reduce_exposure": True}}
