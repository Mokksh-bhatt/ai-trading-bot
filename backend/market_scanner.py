from pybit.unified_trading import HTTP
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
BYBIT_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_SECRET = os.getenv("BYBIT_API_SECRET")

# Initialize a read-only client for scanning (doesn't strictly need keys for public data, but good for rate limits)
scanner_client = HTTP(
    testnet=False, # Public data doesn't matter, but mainnet has better volume stats
    api_key=BYBIT_KEY,
    api_secret=BYBIT_SECRET,
    max_retries=1
)

def fetch_trending_social_velocity():
    """
    Pulls the global top trending coins from CoinGecko's public API to use as a 
    Social Velocity / Retail Flow proxy, completely for free without API keys.
    """
    trending_symbols = set()
    try:
        res = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=5)
        if res.status_code == 200:
            data = res.json()
            for coin in data.get("coins", []):
                sym = coin["item"]["symbol"].upper()
                trending_symbols.add(sym + "USDT")
    except Exception as e:
        print(f"[SCANNER] Could not fetch social velocity data: {e}")
    return trending_symbols

def fetch_market_opportunities(top_n: int = 3):
    """
    Scans the entire Bybit linear futures market for highly volatile, high-volume trading opportunities.
    Implements a strict Wash-Trade Filter to reject manipulated assets.
    """
    try:
        trending_symbols = fetch_trending_social_velocity()
        response = scanner_client.get_tickers(category="linear")
        tickers = response.get("result", {}).get("list", [])
        
        valid_candidates = []
        
        for t in tickers:
            symbol = t.get("symbol", "")
            # Only trade USDT pairs for consistent dollar-value math
            if not symbol.endswith("USDT"):
                continue
                
            turnover = float(t.get("turnover24h", 0))
            price_pct_change = float(t.get("price24hPcnt", 0))
            last_price = float(t.get("lastPrice", 0))
            
            # Filter 1: Liquidity threshold (must have > $10m 24h turnover)
            if turnover < 10_000_000:
                continue
                
            # Filter 2: The Wash-Trade Filter
            # If an asset has massive volume (top 20%) but has barely moved (< 5%), it's being wash traded or suppressed.
            # Reject it to prevent the AI from getting chopped up in artificial sideways chop.
            if turnover > 50_000_000 and abs(price_pct_change) < 0.05:
                continue # Reject
                
            # Filter 3: Minimum volatility
            # We want coins that are ACTUALLY moving so the AI has a trend to ride.
            if abs(price_pct_change) < 0.06:
                continue
                
            # Calculate composite base score
            base_score = abs(price_pct_change) * turnover
            
            funding_rate = float(t.get("fundingRate", 0))
            is_trending = symbol in trending_symbols
            
            # Apply Social Velocity Multiplier if it's globally trending on CoinGecko
            if is_trending:
                base_score *= 3.0
                print(f"[SCANNER] Social Velocity Spike Detected on {symbol}! Applying 3x multiplier.")
                
            valid_candidates.append({
                "symbol": symbol,
                "asset_class": "crypto",
                "is_trending_socially": is_trending,
                "price_change_24h_pct": price_pct_change * 100,
                "turnover_24h_usdt": turnover,
                "funding_rate_8h_pct": funding_rate * 100,
                "last_price": last_price,
                "score": base_score
            })
            
        # Sort by our composite momentum score descending
        valid_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Return the full dictionaries so the AI can see the actual volatility and turnover
        return valid_candidates[:top_n]
        
    except Exception as e:
        print(f"[SCANNER ERROR] Failed to fetch market opportunities: {e}")
        # Fallback to defaults if API fails
        return [("BTCUSDT", "crypto"), ("ETHUSDT", "crypto"), ("SOLUSDT", "crypto")]

if __name__ == "__main__":
    print("Running standalone market scan...")
    targets = fetch_market_opportunities(5)
    print(f"Top Targets Found: {targets}")
