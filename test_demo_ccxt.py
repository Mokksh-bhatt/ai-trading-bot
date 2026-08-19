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
    # Point ccxt to Bybit Demo Trading
    exchange.urls['api'] = exchange.urls['demotrading']
    
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {}).get('free', 0)
    print("Demo Balance:", usdt)
except Exception as e:
    print(f"Bybit Order Error: {e}")
