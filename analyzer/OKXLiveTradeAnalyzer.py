import backtrader as bt

from model import TradeRecord
from loguru import logger
log = logger.bind(name="strategy_analyzer")

class OKXLiveTradeAnalyzer(bt.Analyzer):
    def __init__(self, db, group_id=None):
        self.db = db
        self.strategy_id = id(self)
        self.group_id = self.strategy_id
        if group_id:
            self.group_id = group_id
        log.info("Init StrategyAnalyzer")

    def notify_order(self, order):
        price = order.price
        exec_type = order.ExecTypes[order.exectype]
        status = order.getstatusname()
        side = order.OrdTypes[order.ordtype]
        size = order.size
        executed_price = order.executed_price
        executed_size = order.executed_size
        cost = order.cost
        fee = order.fee
        clientOrderId = order.clientOrderId
        tradeid = order.tradeid
        symbol = order.symbol
        timestamp = order.timestamp
        record = TradeRecord(
            st_id=self.strategy_id,
            group_id=self.group_id,
            trade_id=tradeid,
            client_order_id=clientOrderId,
            symbol=symbol,
            timestamp=timestamp,
            exec_type=exec_type,
            price=price,
            status=status,
            side=side,
            size=size,
            executed_price=executed_price,
            executed_size=executed_size,
            cost=cost,
            fee=fee,
        )

        self.db.merge(record)
        self.db.commit()
        log.info(record.to_dict())

    def stop(self):
        pass

    def __del__(self):
        self.db.close()




