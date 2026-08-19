import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv('.env')

try:
    session = HTTP(
        demo=True,
        api_key='AsPjoYquz8XPN0BCzd',
        api_secret='J9TThOHlNG67a769zj6Ej59IeSK1AQWd567j',
    )
    print(session.get_wallet_balance(accountType="UNIFIED"))
except Exception as e:
    print(f"Pybit Error: {e}")
