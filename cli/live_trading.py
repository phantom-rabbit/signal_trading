import datetime
import os.path
import sys

import backtrader as bt
import click
import toml
from analyzer import PositionReturn, OKXLiveTradeAnalyzer
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.TradeModel import Base
from broker import CCXTBroker, CCXTData
from strategy import Busy
import signal
from .utils import COMMA_SEPARATED_LIST, COMMA_SEPARATED_LIST_INT


@click.group()
@click.pass_context
@click.option('--config', "-c", "config", type=click.File('r'), required=True, help='Path to the configuration file.')
def live_trading(ctx, config):
    """实盘交易"""
    ctx.obj = toml.load(config)
    # print(ctx.obj['LOG']['level'])
    logger.add(ctx.obj['LOG']['path'], level='DEBUG', format="{time} {level} {message}")


def create_free_data(symbol, interval, sandbox, exchange_id, limit=0):
    data = CCXTData(
        sandbox=sandbox,
        symbol=symbol,
        interval=interval,
        exchange_id=exchange_id,
    )
    if limit != 0:
        data.pre_fetch_data(limit)
    return data

def create_database(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    Base.metadata.create_all(bind=engine)

    return session

def create_broker(apikey, secret, password, symbol, cash, exchange_id, sandbox):
    broker = CCXTBroker(
        api_key=apikey,
        secret=secret,
        password=password,
        symbol=symbol,
        cash=cash,
        exchange_id=exchange_id,
        sandbox=sandbox,
    )

    return broker

@live_trading.command()
@click.pass_context
@click.option('--short_period', type=int, required=True, help="短周期")
@click.option('--long_period', type=int, required=True, help="长周期")
@click.option('--below', type=float, required=True, help="低于周期的百分比买入")
@click.option("--net_profit", type=float, required=True, help="固定收益百分比")
@click.option("--stop_loss", type=float, required=True, help="风险控制百分比")
@click.option('--maxcpus', default=os.cpu_count())
def sma_busy(ctx, short_period, long_period, below, net_profit, stop_loss, maxcpus):
    apikey = ctx.obj['API']['apikey']
    secret = ctx.obj['API']['secret']
    password = ctx.obj['API']['password']
    sandbox = ctx.obj['API']['sandbox']
    id = ctx.obj['API']['id']

    symbol = ctx.obj['TRADE']['symbol']
    interval = ctx.obj['TRADE']['interval']
    cash = ctx.obj['TRADE']['cash']

    # db_path = ctx.obj['DATABASE']['path']
    # session = create_database(db_path)
    data = create_free_data(symbol, interval, sandbox, id, limit=max(short_period, long_period))
    broker = create_broker(apikey=apikey, secret=secret, password=password, symbol=symbol, cash=cash, exchange_id=id, sandbox=sandbox)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcash(cash)
    # cerebro.addanalyzer(OKXLiveTradeAnalyzer, db=session)
    cerebro.setbroker(broker)
    cerebro.addstrategy(
        Busy,
        short_period=short_period,
        long_period=long_period,
        below=below,
        net_profit=net_profit,
        stop_loss=stop_loss,
    )

    # 运行策略
    # 注册信号处理函数
    def signal_handler(signal, frame):
        logger.info("Signal received, stopping...")
        data.stop()
        cerebro.runstop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    cerebro.run()
