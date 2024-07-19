import backtrader as bt
from loguru import logger

class EMA(bt.Strategy):
    params = (
        ('period', 7),
        ('below', 0.05),
        ('above', 0.05),
        ('debug', False),
    )

    def __init__(self):
        self.ema_short = bt.indicators.EMA(self.datas[0], period=self.params.period)
        self._open_order = 0
        self.op = bt.Order.Buy
        logger.info(f"Init EMA strategy params: {self.params.period}")

    def next(self):
        # 获取最近N个Bar的数据
        if len(self.datas[0]) < self.params.period:
            return

        if self.p.debug:
            logger.debug(f"time:{self.datas[0].datetime.datetime(0)} close price:{self.datas[0].close[0]}")

        if self._open_order != 0:
            return

        # 获取当前头寸
        position = self.getposition(self.data).size
        cash = self.broker.getcash()
        if self.p.debug:
            logger.debug(f"position:{position} cash:{cash} avg_price:{self.ema_short[0]} close:{self.datas[0].close[0]}")

        buy_price = self.ema_short[0] * (1 - self.params.below)
        sell_price = self.ema_short[0] * (1 + self.params.above)
        if self.datas[0].close[0] < buy_price:
            if self.op == bt.Order.Buy:
                number = cash / self.datas[0].close[0]
                size = int(number*10000)/10000 # 保留小数点后4位
                order = self.buy(price=self.datas[0].close[0], size=size, exectype=bt.Order.Limit)
                self._open_order += 1
                if self.p.debug:
                    logger.debug(f"buy order price:{self.datas[0].close[0]} size:{size} exectype:{bt.Order.Limit}")

        elif self.datas[0].close[0] > sell_price:
            if self.op == bt.Order.Sell:
                size = int(position*10000)/10000  # 保留小数点后4位
                order = self.sell(price=self.datas[0].close[0], size=size, exectype=bt.Order.Limit)
                self._open_order += 1
                if self.p.debug:
                    logger.debug(f"sell order price:{self.datas[0].close[0]} size:{size}")

    def notify_order(self, order):
        if order.status == bt.Order.Completed:
            self._open_order -= 1
            action = bt.Order.Sell if order.isbuy() else bt.Order.Buy
            self.op = action


    def stop(self):
        logger.info(f'参数: {self.params.__dict__} 现金: {self.broker.get_cash():.4f} 持仓: {self.getposition(self.data).size:.4f} 总资产: {self.broker.get_value():.4f}')

    def get_decimal_places(self, number):
        """获取小数点后位数"""
        number_str = str(number)
        if '.' in number_str:
            return len(number_str.split('.')[1])
        return 0