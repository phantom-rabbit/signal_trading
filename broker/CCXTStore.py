import sys
from decimal import Decimal, ROUND_DOWN

import ccxt
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed


class MetaSingleton(MetaParams):
    '''Metaclass to make a metaclassed class a singleton'''

    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


class CCXTStore(with_metaclass(MetaSingleton, object)):
    params = (
        ('api_key', ''),
        ('secret', ''),
        ('password', ''),
        ('exchange_id', ''),
        ('sandbox', True),
    )

    BrokerCls = None  # broker class will auto register
    DataCls = None  # data class will auto register

    def __init__(self):
        exchange_class = getattr(ccxt, self.p.exchange_id)

        exchange = exchange_class({
            'apiKey': self.p.api_key,
            'secret': self.p.secret,
            'password': self.p.password,
            'enableRateLimit': True,
        })

        if self.params.sandbox:
            exchange.set_sandbox_mode(True)

        self.exchange = exchange
        self.markets = self.exchange.load_markets()


    def get_balance(self, coin='USDT'):
        balance = self.exchange.fetch_balance(params={
            "ccy": coin
        })
        cash_free = balance['free'][coin]
        return cash_free

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''Returns ``DataCls`` with args, kwargs'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return cls.BrokerCls(*args, **kwargs)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(30))
    def execute_order(self, symbol, side, size, price=None, order_type='limit'):
        try:
            size = self.handler_precision(symbol, size)
            price = self.adjust_price(symbol, side, price)
            logger.debug(
                    f"Executing order: symbol: {symbol}, type: {order_type}, side: {side}, size: {size}, price: {price}")
            order = self.exchange.create_order(symbol, order_type, side, size, price)
            logger.debug(f"Order result: {order}")
            return order
        except Exception as e:
            logger.error(e)
            raise

    def adjust_price(self, symbol, side, price):
        highest_price_limit = self.get_highest_price_limit(symbol, side)
        if side == "buy":
            if price > highest_price_limit:
                logger.warning(
                    f"Side {side} price {price} exceeds highest price limit {highest_price_limit}. Adjusting to limit.")
                price = highest_price_limit
        else:
            if price < highest_price_limit:
                price = highest_price_limit
        return price

    def get_highest_price_limit(self, symbol, side):
        market = self.exchange.market(symbol)
        response = self.exchange.public_get_public_price_limit({
            'instId': market['id']
        })
        if side == 'buy':
            return float(response['data'][0]['buyLmt'])
        else:
            return float(response['data'][0]['sellLmt'])

    @retry(wait=wait_fixed(2))
    def fetch_order(self, oid, symbol):
        logger.debug(f"Fetch_order: {oid}")
        order_info = self.exchange.fetch_order(oid, symbol)
        logger.debug(f"Fetch_order result: {order_info}")
        return order_info

    def handler_precision(self, symbol, value):
        amount_precision = int(abs(Decimal(str(self.markets[symbol]['precision']['amount'])).as_tuple().exponent))
        value = truncate_to_decimal_places(value, amount_precision)
        return value


def truncate_to_decimal_places(number, decimal_places):
    # 确保 decimal_places 是整数
    decimal_places = int(decimal_places)

    # 将数字转换为 Decimal 类型
    decimal_number = Decimal(str(number))

    # 构建截断的格式字符串，例如：'1.00000000' 表示保留 8 位小数
    format_string = '1.' + '0' * decimal_places

    # 使用 quantize 进行截断，不进行四舍五入
    truncated_number = decimal_number.quantize(Decimal(format_string), rounding=ROUND_DOWN)

    # 去除多余的零
    return truncated_number.normalize()
