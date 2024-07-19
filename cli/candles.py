import click
from broker.OKXData import OKXData
import pandas as pd
from loguru import logger


@click.group()
def candles():
    pass


@candles.command()
@click.option('--symbol', default='BTC/USDT', help='交易对 BTC/USDT')
@click.option('--interval', default='1m', help='交易间隔，查看okx candles参数 1m/3m/5m/....')
@click.option('--start', default='2023-01-01 00:00:00', help='2023-01-01 00:00:00')
@click.option('--end', default='2023-01-02 00:00:00', help='2023-01-02 00:00:00')
def history(symbol, interval, start, end):
    """获取历史数据"""
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    okx_data = OKXData(online_data=False, symbol=symbol, limit=100, interval=interval, debug=True, fromdate=start,
                       todate=end)

    file_name = f"{str.replace(symbol, '/', '_')}_{interval}_{start}_{end}.csv"
    okx_data.save_(file_name)
    logger.info(f"save to {file_name}")