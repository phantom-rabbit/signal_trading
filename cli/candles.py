import os.path
import sys

import click
from broker import CCXTData
import pandas as pd
from loguru import logger
import re


@click.group()
@click.pass_context
def candles(ctx):
    pass


@candles.command()
@click.option('--sandbox', default=True, is_flag=True,  help='模拟盘/实盘')
@click.option('--exchange_id', required=True, help='交易所ID')
@click.option('--symbol', default='BTC/USDT', help='交易对 BTC/USDT')
@click.option('--interval', default='1m', help='交易间隔，查看okx candles参数 1m/3m/5m/....')
@click.option('--start', default='2023-01-01 00:00:00', help='2023-01-01 00:00:00')
@click.option('--end', default='2023-01-02 00:00:00', help='2023-01-02 00:00:00')
@click.option('--output', default='', help='输出文件存放位置')
def history(sandbox, exchange_id, symbol, interval, start, end, output):
    """获取历史数据"""
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    okx_data = CCXTData(
        sandbox=sandbox,
        symbol=symbol,
        interval=interval,
        exchange_id=exchange_id,
       )

    file_name = f"{symbol}_{interval}_{start}_{end}"

    filename = clean_filename(filename=file_name)
    if output:
        os.makedirs(output, exist_ok=True)
        filename = os.path.join(output, filename)
    okx_data.save_to_csv(fromdate=start, todate=end, path=filename)


def clean_filename(filename):
    # 去掉空格和斜杠
    cleaned_filename = filename.replace(" ", "").replace("/", "").replace("00:00:00", "")

    # 使用正则表达式去掉时分秒部分
    cleaned_filename = re.sub(r'(\d{4}-\d{2}-\d{2})\s\d{2}:\d{2}:\d{2}', r'\1', cleaned_filename)
    cleaned_filename = re.sub(r'(\d{4}-\d{2}-\d{2})\s\d{2}:\d{2}:\d{2}', r'\1', cleaned_filename)

    return cleaned_filename