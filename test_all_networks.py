import time, hashlib, hmac, requests

api_key = 'AsPjoYquz8XPN0BCzd'
api_secret = 'J9TThOHlNG67a769zj6Ej59IeSK1AQWd567j'

def test_api(url):
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
    try:
        response = requests.get(f'{url}/v5/user/query-api', headers=headers).json()
        print(f"{url} -> {response}")
    except Exception as e:
        print(f"{url} Error -> {e}")

test_api('https://api-testnet.bybit.com')
test_api('https://api.bybit.com')
test_api('https://api-demo.bybit.com')
