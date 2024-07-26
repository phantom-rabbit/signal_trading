import sys
from datetime import datetime, timedelta
import time
import ccxt
import backtrader as bt
import pytz
from loguru import logger
import pandas as pd

class CCXTData(bt.DataBase):
    params = (
        ('sandbox', True),
        ('exchange_id', ''),
        ('symbol', 'BTC/USDT'),
        ('interval', '1m'),
    )

    def __init__(self):
        exchange_class = getattr(ccxt, self.p.exchange_id)
        exchange = exchange_class({
            'enableRateLimit': True,
        })

        if self.params.sandbox:
            exchange.set_sandbox_mode(True)

        self.exchange = exchange
        self.last_ts = 0
        self.ohlcv = []

    def start(self):
        super(CCXTData, self).start()

    def stop(self):
        pass

    def haslivedata(self):
        if len(self.ohlcv) != 0:
            return True
        else:
            return False

    def islive(self):
        return True

    def _load(self):
        try:
            if not self.ohlcv:
                while not self.ohlcv:
                    time.sleep(2)
                    utc_now = datetime.utcnow() + timedelta(hours=8)
                    to_ = int(utc_now.timestamp() * 1000)
                    from_ = to_ - self._interval_to_milliseconds(self.p.interval)

                    if self.is_same_minute(to_, self.last_ts):
                        continue
                    self.fetch_data(from_, to_)

            if self.ohlcv:
                ohlc = self.ohlcv.pop(0)
                ohlc[0] = bt.date2num(ohlc[0])
                self.lines.datetime[0] = ohlc[0]
                self.lines.open[0] = ohlc[1]
                self.lines.high[0] = ohlc[2]
                self.lines.low[0] = ohlc[3]
                self.lines.close[0] = ohlc[4]
                self.lines.volume[0] = ohlc[5]

                return True
            else:
                print(111)
                return False
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False

    def is_same_minute(self, timestamp1, timestamp2):
        dt1 = datetime.utcfromtimestamp(timestamp1 / 1000) + timedelta(hours=8)
        dt2 = datetime.utcfromtimestamp(timestamp2 / 1000) + timedelta(hours=8)

        return dt1.strftime('%Y-%m-%d %H:%M') == dt2.strftime('%Y-%m-%d %H:%M')

    def _interval_to_milliseconds(self, interval):
        unit = interval[-1]
        amount = int(interval[:-1])
        if unit == 'm':
            return amount * 60 * 1000
        elif unit == 'h':
            return amount * 3600 * 1000
        elif unit == 'd':
            return amount * 86400 * 1000
        else:
            raise ValueError(f"Invalid interval: {interval}")

    def convert_timestamp_to_china_time(self, timestamp_ms):
        # 将毫秒时间戳转换为秒
        timestamp_sec = timestamp_ms
        # 将时间戳转换为UTC时间
        utc_time = datetime.utcfromtimestamp(timestamp_sec)
        # 定义中国时区
        china_tz = pytz.timezone('Asia/Shanghai')
        # 转换为中国时间
        china_time = utc_time.replace(tzinfo=pytz.utc).astimezone(china_tz)
        return china_time

    def pre_fetch_data(self, limit):
        """预加载数据"""
        logger.info(f"pre fetch data {limit}")
        utc_now = datetime.utcnow() + timedelta(hours=8)
        to_ = int(utc_now.timestamp() * 1000)
        from_ = to_ - self._interval_to_milliseconds(self.p.interval) * limit
        self.fetch_data(from_, to_, limit=100)

    def fetch_data(self, from_timestamp, to_timestamp, limit=10):
        try:
            current_timestamp = from_timestamp
            while current_timestamp < to_timestamp:
                ohlcvs = self.exchange.fetch_ohlcv(self.p.symbol, self.p.interval, since=current_timestamp, limit=limit)
                if ohlcvs:
                    back_one = ohlcvs[-1][0]
                    for ohlcv in ohlcvs:
                        if ohlcv[0] > self.last_ts:
                            index_timestamp = ohlcv[0]
                            ohlcv[0] = datetime.fromtimestamp(ohlcv[0]/1000)
                            self.last_ts = index_timestamp
                            self.ohlcv.append(ohlcv)
                    logger.debug(
                        f"Fetched data point: {datetime.fromtimestamp(index_timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')} limit {len(ohlcvs)}")
                    current_timestamp = back_one + 1  # 更新当前时间戳为最后一个数据点的时间戳+1
                else:
                    break
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise e

    def save_to_csv(self, fromdate, todate, path):
        if fromdate and todate:
            from_timestamp = int(fromdate.timestamp() * 1000)
            to_timestamp = int(todate.timestamp() * 1000)
            if to_timestamp < from_timestamp:
                logger.warning("开始时间小于结束时间")
                sys.exit(1)

            self.fetch_data(from_timestamp, to_timestamp, limit=100)

        else:
            logger.error("时间区间不能为空")
            sys.exit(1)

        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(self.ohlcv, columns=columns)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        path = f"{path}_{self.p.exchange_id}_{'testnet' if self.p.sandbox else 'mainnet'}.csv"
        df.to_csv(path, index=False)
        logger.info(f"save to {path}")

def main():
    cerebro = bt.Cerebro()

    # 添加数据源
    data = CCXTData(
        exchange_id='okx',   # 使用的交易所 ID，如 binance
        symbol='BTC/USDT',       # 交易对
        interval='1m',           # 时间间隔
        sandbox=True             # 是否启用沙盒模式
    )
    data.pre_fetch_data(100)
    cerebro.adddata(data)

    # 添加策略
    cerebro.addstrategy(TestStrategy)

    # 运行回测
    cerebro.run()

if __name__ == '__main__':
    main()
