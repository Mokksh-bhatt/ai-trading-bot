import os, time
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv('.env')

original_time = time.time
time.time = lambda: original_time() - 2.0

try:
    session = HTTP(
        demo=True,
        api_key='AsPjoYquz8XPN0BCzd',
        api_secret='J9TThOHlNG67a769zj6Ej59IeSK1AQWd567j',
    )
    print(session.place_order(
        category="linear",
        symbol="BTCUSDT",
        side="Buy",
        orderType="Market",
        qty="0.001"
    ))
except Exception as e:
    print(f"Pybit Error: {e}")
finally:
    time.time = original_time
