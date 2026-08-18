import ccxt

try:
    # Initialize bybit
    exchange = ccxt.bybit({'enableRateLimit': True})
    exchange.set_sandbox_mode(True)
    
    markets = exchange.load_markets()
    
    # Check what BTC/USDT linear swap is called in CCXT bybit
    target_symbols = ['BTC/USDT', 'BTC/USDT:USDT', 'BTCUSDT']
    for sym in target_symbols:
        if sym in markets:
            print(f"Found Bybit market: {sym}")
            m = markets[sym]
            print(f"Type: {m['type']}, Contract: {m.get('contract', False)}, Linear: {m.get('linear', False)}")
            
except Exception as e:
    print(f"Bybit CCXT Error: {e}")
