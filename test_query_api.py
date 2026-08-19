import time, hashlib, hmac, requests

api_key = '6VQmAJqyLsQR1c3act'
api_secret = 'vk26jbX7mB7Pl2VudWns3JRixOM128FPeiaD'

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

print("Raw HTTP Result:", requests.get('https://api-testnet.bybit.com/v5/user/query-api', headers=headers).json())
