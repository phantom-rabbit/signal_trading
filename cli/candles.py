import os.path
import sys

import click
from broker.OKXData import OKXData
import pandas as pd
from loguru import logger
import re


@click.group()
@click.pass_context
def candles(ctx):
    pass


@candles.command()
@click.option('--symbol', default='BTC/USDT', help='交易对 BTC/USDT')
@click.option('--interval', default='1m', help='交易间隔，查看okx candles参数 1m/3m/5m/....')
@click.option('--start', default='2023-01-01 00:00:00', help='2023-01-01 00:00:00')
@click.option('--end', default='2023-01-02 00:00:00', help='2023-01-02 00:00:00')
@click.pass_context
def history(ctx, symbol, interval, start, end):
    workdir = ctx.obj['work_dir']
    """获取历史数据"""
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    okx_data = OKXData(online_data=False, symbol=symbol, limit=100, interval=interval, debug=True, fromdate=start,
                       todate=end)

    file_name = f"{symbol}_{interval}_{start}_{end}.csv"
    filename = clean_filename(filename=file_name)
    directory = os.path.join(workdir, "candles")
    filename = os.path.join(directory, filename)
    os.makedirs(directory, exist_ok=True)
    okx_data.save_(filename)
    logger.info(f"save to {filename}")

def clean_filename(filename):
    # 去掉空格和斜杠
    cleaned_filename = filename.replace(" ", "").replace("/", "")

    # 使用正则表达式去掉时分秒部分
    cleaned_filename = re.sub(r'(\d{4}-\d{2}-\d{2})\s\d{2}:\d{2}:\d{2}', r'\1', cleaned_filename)
    cleaned_filename = re.sub(r'(\d{4}-\d{2}-\d{2})\s\d{2}:\d{2}:\d{2}', r'\1', cleaned_filename)

    return cleaned_filename