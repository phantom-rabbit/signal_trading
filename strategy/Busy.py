import backtrader as bt
from loguru import logger


class Busy(bt.Strategy):
    """
    策略描述：
        争取在震荡趋势中寻求百分之百胜率
        1.	开单: 在均线period之下的某个百分比below买入。
        2.	止盈: 当盈利达到买单本金的某个百分比net_profit时卖出。
        3.	止损: 当价格跌破长均线框体的某个百分比时卖出。
        4.	风险控制: 当价格跌破长均线框体并且趋势没有平稳时，不进行新的交易。
    """

    params = (
        ('short_period', 50),  # 短期均线周期
        ('long_period', 200),  # 长期均线周期
        ('below', 0.02),  # 买入百分比
        ('net_profit', 0.05),  # 止盈百分比
        ('stop_loss', 0.03),  # 止损百分比
        ('debug', True),
    )

    def __init__(self):
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)
        self.buy_price = None
        self._open_order = None
        self.op = bt.Order.Buy
        logger.info(f"Init Busy strategy params: {self.params.__dict__}")

    def next(self):
        # 获取最近N个Bar的数据
        if len(self.datas[0]) < self.params.long_period:
            if self.p.debug:
                logger.debug(f"time:{self.datas[0].datetime.datetime(0)} close price:{self.datas[0].close[0]}")
            return
        if self._open_order and self.op == bt.Order.Sell:
            # TODO 达到风险控制，没有完成的买单要及时撤单
            # TODO 已有的买单要及时更新卖价
            # 检查止损条件
            if self.data.close[0] <= self.buy_price * (1 - self.params.stop_loss):
                position = self.getposition(self.data).size
                logger.warning(f"触发止损条件({self.data.close[0] <= self.buy_price * (1 - self.params.stop_loss)})"
                               f"买单价格:{self.buy_price} 当前价格{self.data.close[0]} time:{self.datas[0].datetime.datetime(0)}")
                self.buy_price = 0
                size = position
                self.sell(price=self.data.close[0], size=size, exectype=bt.Order.Limit)
                self._open_order = True
                self.op = bt.Order.Buy
                logger.warning(f"sell stop loss order price:{self.datas[0].close[0]} size:{size}")
            return

        if self._open_order:
            return
        # 风险控制，不开新仓
        if self.data.close[0] < self.long_ma[0]:
            logger.warning(f"触发风险控制,暂停开单 {self.datas[0].datetime.datetime(0)} 当前价低于长均线:{self.data.close[0]}<{self.long_ma[0]}")
            return

        # 获取当前头寸
        position = self.getposition(self.data).size
        cash = self.broker.getcash()

        if self.op == bt.Order.Buy:  # 当前无任何订单
            # 检查开仓条件
            if self.data.close[0] <= self.short_ma[0] * (1 - self.params.below):
                if self.p.debug:
                    logger.debug(f"触发开仓条件:({self.data.close[0]} <= {self.short_ma[0] * (1 - self.params.below)}) "
                                 f"position:{position} "
                                 f"cash:{cash} "
                                 f"short_ma:{self.short_ma[0]} "
                                 f"time: {self.datas[0].datetime.datetime(0)}")

                self.buy_price = self.data.close[0]
                size = cash / self.buy_price
                self.buy(price=self.buy_price, size=size, exectype=bt.Order.Limit)
                self._open_order = True
                if self.p.debug:
                    logger.debug(f"buy order price:{self.buy_price} size:{size} exectype:{bt.Order.Limit}")

        else:  # 当前已存在买单，
            # 检查止盈条件
            if self.data.close[0] >= self.buy_price * (1 + self.params.net_profit):
                logger.debug(f"触发止盈条件:({self.data.close[0]} >= {self.buy_price * (1 + self.params.net_profit)} "
                             f"position:{position} "
                             f"cash:{cash} "
                             f"buy_price:{self.buy_price} "
                             f"time:{self.datas[0].datetime.datetime(0)} ")
                self.buy_price = 0
                size = position
                # TODO 使用最高价卖出
                self.sell(price=self.data.close[0], size=size, exectype=bt.Order.Limit)
                self._open_order = True
                if self.p.debug:
                    logger.debug(f"sell order price:{self.datas[0].close[0]} size:{size}")



    def notify_order(self, order):
        if order.status == bt.Order.Completed:
            self._open_order = False
            action = bt.Order.Sell if order.isbuy() else bt.Order.Buy
            self.op = action
            # 获取当前头寸
            position = self.getposition(self.data).size
            cash = self.broker.getcash()
            logger.info(f"position:{position:.8e} cach:{cash:.4e}")