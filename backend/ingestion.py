import yfinance as yf
import ccxt
from datetime import datetime, timezone
import pandas as pd
from backend.models import MarketSnapshot

def calculate_ta(prices: list) -> dict:
    if len(prices) < 20:
        return {"RSI_14": 50.0, "SMA_9": 0.0, "SMA_20": 0.0}
    
    s = pd.Series(prices)
    sma_9 = s.rolling(window=9).mean().iloc[-1]
    sma_20 = s.rolling(window=20).mean().iloc[-1]
    
    delta = s.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_14 = rsi.iloc[-1]
    
    return {
        "RSI_14": round(float(rsi_14), 2) if not pd.isna(rsi_14) else 50.0,
        "SMA_9": round(float(sma_9), 2),
        "SMA_20": round(float(sma_20), 2)
    }

def get_crypto_snapshot(symbol: str) -> MarketSnapshot:
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker(symbol)
    
    price = float(ticker['last']) if ticker.get('last') is not None else 0.0
    volume = float(ticker['baseVolume']) if ticker.get('baseVolume') is not None else 0.0
    
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=30)
    prices = [row[4] for row in ohlcv]
    ta_metrics = calculate_ta(prices)
    
    context = {
        "24h_high": ticker.get('high'),
        "24h_low": ticker.get('low'),
        "24h_change_pct": ticker.get('percentage'),
        "TA": ta_metrics
    }
    
    return MarketSnapshot(
        symbol=symbol,
        asset_class="crypto",
        price=price,
        volume=volume,
        timestamp=datetime.now(timezone.utc),
        context=context
    )

def get_stock_snapshot(symbol: str) -> MarketSnapshot:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        raise ValueError(f"No recent data available for {symbol}")
    
    last_row = data.iloc[-1]
    
    # Enrichment
    try:
        info = ticker.info
        news = ticker.news
        recent_headlines = [n.get("title") for n in news[:3]] if news else []
    except Exception:
        info = {}
        recent_headlines = []
    
    prices = data['Close'].tolist()
    ta_metrics = calculate_ta(prices)
    
    context = {
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "market_cap": info.get("marketCap", "Unknown"),
        "forward_pe": info.get("forwardPE", "Unknown"),
        "recent_news": recent_headlines,
        "TA": ta_metrics
    }
    
    return MarketSnapshot(
        symbol=symbol,
        asset_class="stock",
        price=float(last_row['Close']),
        volume=float(last_row['Volume']),
        timestamp=datetime.now(timezone.utc),
        context=context
    )

def fetch_market_snapshot(symbol: str, asset_class: str) -> MarketSnapshot:
    if asset_class == "crypto":
        return get_crypto_snapshot(symbol)
    elif asset_class == "stock":
        return get_stock_snapshot(symbol)
    else:
        raise ValueError(f"Unknown asset class: {asset_class}")

def fetch_fast_price(symbol: str, asset_class: str) -> float:
    """Ultra-fast price poll to avoid API rate limits during High Frequency Execution"""
    try:
        if asset_class == "crypto":
            exchange = ccxt.binance()
            ticker = exchange.fetch_ticker(symbol)
            return float(ticker['last']) if ticker.get('last') is not None else 0.0
        elif asset_class == "stock":
            ticker = yf.Ticker(symbol)
            return float(ticker.fast_info['lastPrice'])
    except Exception:
        return 0.0
    return 0.0

def fetch_historical_prices(symbol: str, asset_class: str):
    history = []
    if asset_class == "crypto":
        exchange = ccxt.binance()
        # Fetch last 60 minutes
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=60)
        for row in ohlcv:
            # row: [timestamp, open, high, low, close, volume]
            dt = datetime.fromtimestamp(row[0]/1000, tz=timezone.utc).isoformat()
            history.append({"time": dt, "price": row[4]})
    elif asset_class == "stock":
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        # Tail last 60 rows
        data = data.tail(60)
        for index, row in data.iterrows():
            history.append({"time": index.isoformat(), "price": float(row['Close'])})
    return history
