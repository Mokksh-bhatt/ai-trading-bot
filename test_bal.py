from pybit.unified_trading import HTTP
import os
session = HTTP(demo=True, api_key='AsPjoYquz8XPN0BCzd', api_secret='J9TThOHlNG67a769zj6Ej59IeSK1AQWd567j')
bal = session.get_wallet_balance(accountType="UNIFIED")
print("Balance:", bal)
