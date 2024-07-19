import time
from datetime import datetime

import backtrader as bt
import ccxt
import pandas as pd
import pytz
from loguru import logger
from threading import Lock


class OKXData(bt.DataBase):
    params = (
        ('online_data', True),
        ('symbol', 'BTC/USDT'),
        ('interval', '1m'),
        ('is_testnet', False),
        ('limit', 1),
        ('debug', False),
        ('fromdate', None),  # 回测开始时间，默认为None
        ('todate', None),    # 回测结束时间，默认为None
    )

    def __init__(self):
        super(OKXData, self).__init__()
        self.exchange = ccxt.okx({
            'enableRateLimit': True,
        })
        if self.p.is_testnet:
            self.exchange.set_sandbox_mode(True)

        self.interval = self.p.interval

        self.data_lock = Lock()  # 锁对象，用于线程安全
        self.has_livedata = False
        self.ohlcv = []
        self.last_ts = 0
        self.stop_signal = False
        if self.p.online_data:
            logger.info(f"Initialized OKXData with symbol: {self.p.symbol} and interval: {self.p.interval} for live data")
        else:
            logger.info(f"Initialized OKXData with symbol: {self.p.symbol} and interval: {self.p.interval} for historical data")
            self.fetch_historical_data()

    def start(self):
        pass

    def fetch_data(self):
        current = int(time.time() * 1000)
        try:
            ohlcvs = self.exchange.fetch_ohlcv(self.p.symbol, self.interval, limit=self.p.limit, params={
                "after": current,
            })
            if ohlcvs:
                with self.data_lock:
                    for ohlcv in ohlcvs:
                        tstamp, open_, high, low, close, volume = ohlcv
                        if tstamp > self.last_ts:
                            self.ohlcv.append(ohlcv)
                            self.last_ts = tstamp
                            self.has_livedata = True
                            logger.info(f"Fetched new data: {datetime.fromtimestamp(tstamp / 1000).strftime('%Y-%m-%d %H:%M:%S')} ")

        except Exception as e:
            logger.error(f"Error fetching data: {e}")

    def fetch_historical_data(self):
        with self.data_lock:
            try:
                if self.p.fromdate and self.p.todate:
                    from_timestamp = int(self.p.fromdate.timestamp() * 1000)
                    to_timestamp = int(self.p.todate.timestamp() * 1000)
                    current_timestamp = from_timestamp

                    while current_timestamp < to_timestamp:
                        ohlcvs = self.exchange.fetch_ohlcv(self.p.symbol, self.interval, since=current_timestamp, limit=self.p.limit)
                        if ohlcvs:
                            for ohlcv in ohlcvs:
                                if ohlcv[0] > self.last_ts:  # 去重
                                    self.ohlcv.append(ohlcv)
                                    self.last_ts = ohlcv[0]

                            logger.info(f"Fetched historical data point: {datetime.fromtimestamp(ohlcv[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')} limit {len(ohlcvs)}")
                            current_timestamp = ohlcvs[-1][0] + 1  # 更新当前时间戳为最后一个数据点的时间戳+1
                        else:
                            break  # 如果没有更多数据，退出循环

                    self.has_livedata = True  # 标记为有历史数据加载
                    logger.info(f"Finished fetching historical data from {self.p.fromdate} to {self.p.todate}")

            except Exception as e:
                logger.error(f"Error fetching historical data: {e}")

    def _load(self):
        if self.stop_signal:
            logger.info("stopping data...")
            return False

        while True:
            if self.haslivedata():
                with self.data_lock:
                    self.has_livedata = False
                    candle = self.ohlcv.pop(0)
                    self.lines.datetime[0] = bt.date2num(convert_timestamp_to_china_time(candle[0]/1000))
                    self.lines.open[0] = candle[1]
                    self.lines.high[0] = candle[2]
                    self.lines.low[0] = candle[3]
                    self.lines.close[0] = candle[4]
                    self.lines.volume[0] = candle[5]
                    return True
            else:
                self.fetch_data()

            time.sleep(2)

    def haslivedata(self):
        with self.data_lock:
            return self.has_livedata

    def islive(self):
        return self.p.online_data

    def save_(self, path):
        # 定义字段名称
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        # 创建 DataFrame 并指定列名
        df = pd.DataFrame(self.ohlcv, columns=columns)
        # 保存为 CSV 文件并包含列名
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.to_csv(path, index=False)

    def stop(self):
        self.stop_signal = True

def convert_timestamp_to_china_time(timestamp_ms):
    # 将毫秒时间戳转换为秒
    timestamp_sec = timestamp_ms
    # 将时间戳转换为UTC时间
    utc_time = datetime.utcfromtimestamp(timestamp_sec)
    # 定义中国时区
    china_tz = pytz.timezone('Asia/Shanghai')
    # 转换为中国时间
    china_time = utc_time.replace(tzinfo=pytz.utc).astimezone(china_tz)
    return china_time