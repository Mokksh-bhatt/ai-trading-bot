import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

from pybit.unified_trading import HTTP
import os

api_key = "AsPjoYquz8XPN0BCzd"
api_secret = "J9TThOHlNG67a769zj6Ej59IeSK1AQWd567j"

session = HTTP(demo=True, api_key=api_key, api_secret=api_secret)
try:
    print("Placing test order...")
    res = session.place_order(
        category="linear",
        symbol="DOGEUSDT",
        side="Buy",
        orderType="Market",
        qty="100"
    )
    print("Success:", res)
except Exception as e:
    print(f"Error: {e}")
