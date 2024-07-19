import time

from loguru import logger
import backtrader as bt
from backtrader.utils.py3 import queue, with_metaclass
from .OKXStore import CCXTStore


class Positions:
    size = 0


class CCXTOrder(bt.OrderBase):
    def __init__(self, owner, data, ccxt_order, side, size):
        self.owner = owner
        self.data = data
        self.ccxt_order = ccxt_order
        self.executed_fills = []
        self.ordtype = self.Buy if side == 'buy' else self.Sell
        self.size = size

        super(CCXTOrder, self).__init__()


class MetaCCXTBroker(bt.BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaCCXTBroker, cls).__init__(name, bases, dct)
        CCXTStore.BrokerCls = cls


class OKXBroker(with_metaclass(MetaCCXTBroker, bt.BackBroker)):
    params = (
        ('api_key', ''),
        ('secret', ''),
        ('password', ''),
        ('symbol', 'BTC/USDT'),
        ('is_testnet', True),
        ('cash', 0),
        ('debug', False),
    )

    order_types = {bt.Order.Market: 'market',
                   bt.Order.Limit: 'limit',
                   bt.Order.Stop: 'stop',  # stop-loss for kraken, stop for bitmex
                   bt.Order.StopLimit: 'stop limit'}

    def __init__(self):
        super(OKXBroker, self).__init__()
        logger.info(f"connect to OKEX {'test-net' if self.p.is_testnet else 'main-net'}")
        logger.info(f"set trade cash:{self.p.cash}")
        time.sleep(1)
        self.store = CCXTStore(api_key=self.p.api_key, secret=self.p.secret, password=self.p.password,
                               is_testnet=self.p.is_testnet, cash=self.p.cash, debug=self.p.debug)

        self.cash = self.p.cash
        self.position = Positions()

        self.notifs = queue.Queue()
        self.open_orders = list()

    def start(self):
        logger.info(f"{self.p.symbol} starting...")

    def stop(self):
        logger.info(f"{self.p.symbol} stopping...")

    def get_cash(self):
        return self.cash

    def getposition(self, data):
        return self.position

    def get_value(self):
        return self.cash

    def get_notification(self):
        try:
            return self.notifs.get(False)
        except queue.Empty:
            return None

    def notify(self, order):
        self.notifs.put(order)

    def _submit(self, owner, data, exectype, side, size, price):
        order_type = self.order_types.get(exectype) if exectype else 'market'
        ret_ord = self.store.execute_order(symbol=self.p.symbol, side=side, size=size, price=price,
                                           order_type=order_type)
        order = CCXTOrder(owner, data, None, side, size)
        order.price = price
        order.tradeid = ret_ord['id']
        order.symbol = self.p.symbol
        order.exectype = exectype
        self.open_orders.append(order)
        self.update_order(order)
        return order

    def buy(self, owner, data, size, price=None, exectype=None, tradeid=0, **kwargs):
        side = 'buy'
        del kwargs['parent']
        del kwargs['transmit']
        return self._submit(owner, data, exectype, side, size, price)

    def sell(self, owner, data, size, price=None, exectype=None, tradeid=0, **kwargs):
        side = 'sell'
        del kwargs['parent']
        del kwargs['transmit']
        return self._submit(owner, data, exectype, side, size, price)

    def update_asset(self, order_info):
        if order_info['side'] == 'buy':
            cost = order_info['cost']  # 买单的总花费
            self.cash -= cost
            self.position.size += order_info['filled']
            if order_info['fee']:
                if order_info['fee']["cost"]:
                    self.position.size -= order_info['fee']["cost"]
        elif order_info['side'] == 'sell':
            revenue = order_info['cost']  # 卖单的总收入
            self.cash += revenue
            if order_info['fee']:
                if order_info['fee']["cost"]:
                    self.cash -= order_info['fee']["cost"]
            self.position.size -= order_info['filled']

    def next(self):
        for order in list(self.open_orders):
            self.update_order(order)

    def update_order(self, order):
        _order = self.store.fetch_order(order.tradeid, self.p.symbol)
        status = _order['status']
        if status == 'closed':
            order.completed()
            order.executed_price = _order['average']
            order.executed_size = _order['filled']
            order.cost = _order['cost']
            order.fee = _order['fee']
            order.clientOrderId = _order['clientOrderId']
            order.timestamp = _order['timestamp']
            self.update_asset(_order)
            self.notify(order)
            self.open_orders.remove(order)
