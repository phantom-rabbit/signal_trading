import sys

import backtrader as bt
from loguru import logger


class AscendWave(bt.Strategy):
    """
    AscendWave 是一种基于市场趋势的交易策略，旨在利用上升通道和震荡行情中的市场机会实现盈利。该策略的核心特点如下：
    """

    params = (
        ('short_period', 50),  # 短期均线周期
        ('long_period', 200),  # 长期均线周期
        ('below', 0.02),  # 买入百分比
        ('net_profit', 0.05),  # 止盈百分比
        ('stop_loss', 0.03),  # 止损百分比

        ('rsi_period', 14),  # 波动周期
        ('wave_upper_limit', 50),  # 卖出信号
        ('wave_lower_limit', 30),  # 买入信号

        ('bollinger_period', 20),  # 布林带周期
        ('bollinger_dev', 2.0),  # 布林带范围

        ('threshold', 0.05),  # 变化率阈值
    )

    ASCEND, WAVE = range(2)
    AscendWaveType = "AscendWaveType"

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.low = self.data.low

        self.short_ma = bt.indicators.EMA(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.EMA(self.data.close, period=self.params.long_period)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)
        self.boll = bt.indicators.BollingerBands(period=self.params.bollinger_period,
                                                 devfactor=self.params.bollinger_dev)
        self.op = bt.Order.Buy
        self.commission = 0

        self.wave_order = None

        self._buy_price = 0
        self._open_order = None
        self._buy_interval = 0

    def stop(self):
        size = self.getposition(self.data).size
        cash = self.broker.getcash()
        logger.info(f"cash:{cash} size:{size} commission:{self.commission}")

    def notify_order(self, order):
        logger.info(order)
        if order.status == bt.Order.Completed:
            if order.info[self.AscendWaveType] == self.ASCEND:
                pass
            elif order.info[self.AscendWaveType] == self.WAVE:
                self.wave_order = None
            else:
                logger.error(f"订单类型不匹配: {order.info['type']}")
                sys.exit(1)

            action = bt.Order.Sell if order.isbuy() else bt.Order.Buy
            self.op = action
            self._open_order = False

            # 获取当前头寸
            position = self.getposition(self.data).size
            cash = self.broker.getcash()
            commission = order.size * order.price * 0.001
            if commission < 0:
                commission = commission * -1
            self.commission += commission
            logger.info(f"position:{position:.8f} cach:{cash:.4f} commission:{commission}")

    def next(self):
        if len(self.datas[0]) < max(self.params.short_period, self.params.long_period, self.params.rsi_period):
            logger.debug(f"time:{self.datas[0].datetime.datetime(0)} close price:{self.datas[0].close[0]}")
            return

        self._buy_interval += 1
        # position = self.getposition(self.data).size
        # cash = self.broker.getcash()
        # logger.info(
        #     f"时间:{self.datas[0].datetime.datetime(0)} 持仓:{position:.8f} 现金:{cash:.4f} 买单价:{self._buy_price} 是否存在订单:{self._open_order}")
        # self.risk_management()

        if self._open_order:
            return

        self.select_channel()

    def risk_management(self):
        """ 风险管理 """
        pass

    def select_channel(self):
        """
        通道选择器
        :return:
        """
        current_close = self.data.close[0]

        if self.boll.lines.bot[0] <= current_close < self.boll.lines.mid[0]:
            if current_close < self.boll.lines.mid[0] * (1-self.params.net_profit) :
                logger.info(f"[布林带底部] {current_close} 买单价:{self._buy_price} 当前价:{current_close}")
                order = self._buy_order()
                if order:
                    return

        if self._buy_price != 0:
            if current_close < self._buy_price * (1 - self.params.stop_loss):
                logger.info(
                    f"[止损] {self.datas[0].datetime.datetime(0)} 买单价:{self._buy_price} 当前价:{current_close}")
                order = self._sell_order()
                if order:
                    return


            if current_close > self._buy_price * (1 + self.params.net_profit):
                logger.info(
                    f"[止盈] {self.datas[0].datetime.datetime(0)} 买单价:{self._buy_price} 当前价:{current_close}")
                order = self._sell_order()
                if order:
                    return

    def _buy_order(self):
        current_time = self.datas[0].datetime.datetime(0)
        current_close = self.low[0]
        if self._open_order:
            return
        if self._buy_price != 0:
            return

        cash = self.broker.getcash() - 0.1  # 避免计算精度问题导致溢价
        size = cash / current_close
        order = self.buy(price=current_close, size=size, exectype=bt.Order.Limit, AscendWaveType=self.ASCEND)
        self._open_order = True
        self._buy_price = current_close
        logger.debug(f"买入订单.{current_time} 价格:{current_close} 数量:{size:.8f} cash:{cash}")
        self._buy_interval = 0

        return order

    def _sell_order(self):
        current_time = self.datas[0].datetime.datetime(0)
        current_close = self.data.close[0]
        if self._open_order:
            return
        if self._buy_price == 0:
            return

        size = self.getposition(self.data).size
        order = self.sell(price=self.data.close[0], size=size, exectype=bt.Order.Limit, AscendWaveType=self.ASCEND)
        self._open_order = True
        logger.debug(
            f"卖出订单. {current_time} 买单价格:{self._buy_price} 当前价格:{current_close} 数量:{size:.8f} 浮盈:{((current_close * size) - (self._buy_price * size)):.4f}")
        self._buy_price = 0
        self._buy_interval = 0

        return order

