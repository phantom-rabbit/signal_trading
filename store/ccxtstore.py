import ccxt

class CCXTStore:
    def __init__(self, exchange, api_key=None, secret=None, password=None, timeout=30000):
        self.exchange = getattr(ccxt, exchange)({
            'apiKey': api_key,
            'secret': secret,
            'password': password,
            'timeout': timeout,
            'enableRateLimit': True
        })

    def get_data(self, symbol, timeframe, limit=100):
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return ohlcv