import backtrader as bt
from loguru import logger

class EMA_Crossover(bt.Strategy):
    params = (
        ('short_period', 7),  # 短期EMA周期
        ('long_period', 21),  # 长期EMA周期
        ('debug', False),
    )

    def __init__(self):
        self.ema_short = bt.indicators.EMA(self.datas[0], period=self.params.short_period)
        self.ema_long = bt.indicators.EMA(self.datas[0], period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.ema_short, self.ema_long)
        self._open_order = 0
        self.op = bt.Order.Buy
        logger.info(f"Init EMA Crossover strategy params: {self.params.__dict__}")

    def next(self):
        if len(self.datas[0]) < self.params.long_period:
            return

        if self.p.debug:
            logger.debug(f"time:{self.datas[0].datetime.datetime(0)} close price:{self.datas[0].close[0]}")

        if self._open_order != 0:
            return

        position = self.getposition(self.data).size
        cash = self.broker.getcash()
        if self.p.debug:
            logger.debug(f"position:{position} cash:{cash} short_ema:{self.ema_short[0]} long_ema:{self.ema_long[0]} close:{self.datas[0].close[0]}")

        if self.crossover > 0:  # 黄金交叉，买入
            if self.op == bt.Order.Buy:
                size = cash / self.datas[0].close[0]
                order = self.buy(price=self.datas[0].close[0], size=size, exectype=bt.Order.Limit)
                self._open_order += 1
                if self.p.debug:
                    logger.debug(f"buy order price:{self.datas[0].close[0]} size:{size} exectype:{bt.Order.Limit}")

        elif self.crossover < 0:  # 死亡交叉，卖出
            if self.op == bt.Order.Sell:
                size = position
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
        logger.info(f'参数: short_period={self.params.short_period}, long_period={self.params.long_period} 现金: {self.broker.get_cash():.4f} 持仓: {self.getposition(self.data).size:.4f} 总资产: {self.broker.get_value():.4f}')