import time, hashlib, hmac, requests

api_key = 'guoPdh7F0RScxTcdHV'
api_secret = 'n5b2ytIMkvnpnWmgrVWyYJ9lde2fNDWg4AZG'

timestamp = str(int(time.time() * 1000))
recv_window = str(5000)
param_str = ''

sign_str = timestamp + api_key + recv_window + param_str
signature = hmac.new(bytes(api_secret, 'utf-8'), bytes(sign_str, 'utf-8'), hashlib.sha256).hexdigest()

headers = {
    'X-BAPI-API-KEY': api_key,
    'X-BAPI-SIGN': signature,
    'X-BAPI-TIMESTAMP': timestamp,
    'X-BAPI-RECV-WINDOW': recv_window
}

print(requests.get('https://api-demo.bybit.com/v5/user/query-api', headers=headers).json())
