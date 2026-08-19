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

def calc_rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calc_macd(closes, short_period=12, long_period=26, signal_period=9):
    def ema(data, period):
        k = 2 / (period + 1)
        ema_vals = [data[0]]
        for price in data[1:]:
            ema_vals.append(price * k + ema_vals[-1] * (1 - k))
        return ema_vals
    
    if len(closes) < long_period + signal_period: return "Neutral"
    short_ema = ema(closes, short_period)
    long_ema = ema(closes, long_period)
    macd_line = [s - l for s, l in zip(short_ema, long_ema)]
    signal_line = ema(macd_line, signal_period)
    hist = macd_line[-1] - signal_line[-1]
    if hist > 0 and macd_line[-1] > macd_line[-2]: return "Bullish Cross / Growing"
    elif hist < 0 and macd_line[-1] < macd_line[-2]: return "Bearish Cross / Growing"
    return "Neutral"

def calc_bollinger(closes, period=20, std_dev=2):
    if len(closes) < period: return "Neutral"
    recent = closes[-period:]
    sma = sum(recent) / period
    variance = sum((x - sma) ** 2 for x in recent) / period
    import math
    sd = math.sqrt(variance)
    upper = sma + (sd * std_dev)
    lower = sma - (sd * std_dev)
    last = closes[-1]
    if last >= upper: return "Touching Upper Band (Overbought)"
    elif last <= lower: return "Touching Lower Band (Oversold)"
    return "Inside Bands"

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
            if turnover > 50_000_000 and abs(price_pct_change) < 0.05:
                continue # Reject
                
            # Filter 3: Minimum volatility
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
        
        top_candidates = valid_candidates[:top_n]
        
        # Calculate Technical Indicators (RSI, MACD, Bollinger Bands) for the Top N coins
        for c in top_candidates:
            symbol = c["symbol"]
            try:
                # Fetch 15-minute candle data (last 50 candles)
                klines = scanner_client.get_kline(category="linear", symbol=symbol, interval="15", limit=50)
                list_data = klines.get("result", {}).get("list", [])
                list_data.reverse() # Reverse to chronological order (oldest to newest)
                closes = [float(candle[4]) for candle in list_data]
                
                if len(closes) >= 35:
                    c["RSI_14"] = calc_rsi(closes)
                    c["MACD_Histogram"] = calc_macd(closes)
                    c["Bollinger_Band"] = calc_bollinger(closes)
                else:
                    c["RSI_14"] = 50.0
                    c["MACD_Histogram"] = "Neutral"
                    c["Bollinger_Band"] = "Inside Bands"
            except Exception as e:
                print(f"[SCANNER] Failed to calc tech indicators for {symbol}: {e}")
                c["RSI_14"] = 50.0
                c["MACD_Histogram"] = "Neutral"
                c["Bollinger_Band"] = "Inside Bands"
                
        # Return the full dictionaries so the AI can see the actual volatility, turnover, and tech indicators
        return top_candidates
        
    except Exception as e:
        print(f"[SCANNER ERROR] Failed to fetch market opportunities: {e}")
        # Fallback to defaults if API fails
        return [("BTCUSDT", "crypto"), ("ETHUSDT", "crypto"), ("SOLUSDT", "crypto")]

if __name__ == "__main__":
    print("Running standalone market scan...")
    targets = fetch_market_opportunities(5)
    print(f"Top Targets Found: {targets}")
