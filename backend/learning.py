import json
import os
import requests
from backend.db import get_db_connection

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "long_term_memory.json")

def generate_long_term_memory(model_name: str = "qwen2.5-coder:7b"):
    """Runs a self-reflection prompt on the last 50 trades to generate persistent strategy rules."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch up to 50 last closed trades for the AI to review
    cursor.execute("""
        SELECT symbol, entry_price, exit_price, pnl_pct, reasoning_text 
        FROM trades 
        WHERE model_name = 'OllamaTrader' AND status = 'closed' 
        ORDER BY id DESC LIMIT 50
    """)
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if len(trades) < 5:
        # Not enough data to formulate long-term rules yet
        return

    print("[LEARNING ENGINE] Analyzing past trades for long-term strategy adaptation...", flush=True)

    # Prepare prompt for Ollama
    prompt = f"""
You are a Master Trading Coach reviewing the historical performance of a high-frequency trading bot.
Below are its most recent {len(trades)} trades.

Trades:
{json.dumps(trades, indent=2)}

Your objective is to extract the 3 most critical, absolute RULES for future trading based on these results. 
What specific behaviors led to massive losses (negative pnl_pct)? What led to wins?

Provide exactly 3 concise bullet points defining the ultimate strategy rules the bot must follow going forward to stop losing money and maximize wins. Do not write introductory or closing text. Just output a valid JSON object.

Expected JSON format:
{{
    "learned_rules": [
        "Rule 1...",
        "Rule 2...",
        "Rule 3..."
    ]
}}
"""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        result_json = response.json().get("response", "{}")
        decision = json.loads(result_json)
        
        rules = decision.get("learned_rules", [])
        if rules:
            with open(MEMORY_FILE, "w") as f:
                json.dump({"learned_rules": rules}, f, indent=4)
            print(f"[LEARNING ENGINE] Successfully updated Long-Term Memory with {len(rules)} new rules.", flush=True)
            
    except Exception as e:
        print(f"[LEARNING ENGINE] Failed to generate memory: {e}", flush=True)

def get_learned_rules() -> list:
    """Retrieves the current long-term memory rules from disk."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                return data.get("learned_rules", [])
        except Exception:
            return []
    return []
