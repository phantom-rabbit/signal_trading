import backtrader as bt


class PositionReturn(bt.Analyzer):
    def __init__(self):
        self.cash = 0
        self.value = 0
        self.fundvalue = 0
        self.shares = 0

    def notify_fund(self, cash, value, fundvalue, shares):
        self.cash = cash
        self.value = value
        self.fundvalue = fundvalue
        self.shares = shares

    def get_analysis(self):
        return {
            'cash': self.cash,
            'value': self.value,
            'fundvalue': self.fundvalue,
            'shares': self.shares,
        }