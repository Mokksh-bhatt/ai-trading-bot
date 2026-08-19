import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

from pybit.unified_trading import HTTP
api_key = "AsPjoYquz8XPN0BCzd"
api_secret = "J9TThOHlNG67a769zj6Ej59IeSK1AQWd567j"

print("Testing Mainnet...")
try:
    session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)
    bal = session.get_wallet_balance(accountType="UNIFIED")
    print("Mainnet Success!")
except Exception as e:
    print(f"Mainnet Error: {e}")

print("Testing Testnet...")
try:
    session = HTTP(testnet=True, api_key=api_key, api_secret=api_secret)
    bal = session.get_wallet_balance(accountType="UNIFIED")
    print("Testnet Success!")
except Exception as e:
    print(f"Testnet Error: {e}")

print("Testing Demo...")
try:
    session = HTTP(demo=True, api_key=api_key, api_secret=api_secret)
    bal = session.get_wallet_balance(accountType="UNIFIED")
    print("Demo Success!")
except Exception as e:
    print(f"Demo Error: {e}")
