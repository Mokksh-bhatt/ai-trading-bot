import ccxt, os
from dotenv import load_dotenv

load_dotenv('.env')
try:
    exchange = ccxt.bybit({
        'apiKey': 'AsPjoYquz8XPN0BCzd',
        'secret': 'J9TThOHlNG67a769zj6Ej59IeSK1AQWd567j',
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    exchange.urls['api'] = exchange.urls['demotrading']
    
    # Try fetching positions instead of balance, or just placing a small order
    order = exchange.create_market_order('BTC/USDT:USDT', 'buy', 0.001)
    print("Demo Order Successful!", order)
except Exception as e:
    print(f"Bybit Order Error: {e}")
