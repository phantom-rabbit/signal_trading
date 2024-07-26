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
from strategy.Oscillation import Oscillation
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

def init_broker(args, limit):
    apikey = args['API']['apikey']
    secret = args['API']['secret']
    password = args['API']['password']
    sandbox = args['API']['sandbox']
    exchange_id = args['API']['id']
    symbol = args['TRADE']['symbol']
    interval = args['TRADE']['interval']
    cash = args['TRADE']['cash']
    cerebro = bt.Cerebro()
    datasource = create_free_data(symbol, interval, sandbox, exchange_id, limit)
    broker = create_broker(apikey=apikey, secret=secret, password=password, symbol=symbol, cash=cash, exchange_id=exchange_id,
                           sandbox=sandbox)

    cerebro.adddata(datasource)
    cerebro.setbroker(broker)
    return cerebro

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
@click.option('--short_period', default=60, type=int, help="短周期")
@click.option('--long_period', default=80, type=int, help="长周期")
@click.option('--below', default=0.1, type=float, help="低于周期的百分比买入")
@click.option("--net_profit", default=0.1, type=float,  help="固定收益百分比")
@click.option("--stop_loss", default=0.1, type=float,  help="风险控制百分比")
def sma_busy(ctx, short_period, long_period, below, net_profit, stop_loss):
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
    broker = create_broker(apikey=apikey, secret=secret, password=password, symbol=symbol, cash=cash, exchange_id=id,
                           sandbox=sandbox)
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


@live_trading.command()
@click.pass_context
@click.option('--boll_period', type=int, default=60, required=True, help="布林带的周期长度")
@click.option('--boll_dev', type=float, default=3.0, required=True, help="布林带的标准差倍数")
@click.option('--rsi_period', type=int, default=80, required=True, help="RSI周期")
@click.option('--rsi_buy_signal', type=float, default=41.5, required=True, help="买入信号")
@click.option('--stop_loss', type=float, default=0.1, required=True, help="止损百分比")
def oscillation(ctx, boll_period, boll_dev, rsi_period, rsi_buy_signal, stop_loss):
    """
        根据RSI买入信号进行买入，在超过布林带上限卖出
    """

    cash = ctx.obj['TRADE']['cash']
    symbol = ctx.obj['TRADE']['symbol']
    logger.info("根据RSI买入信号进行买入，在超过布林带上限卖出")
    logger.info(f"布林带周期:{boll_period} "
                f"布林带的标准差倍数:{boll_dev} "
                f"RSI周期:{rsi_period} "
                f"买入信号:{rsi_buy_signal} "
                f"止损百分比:{stop_loss * 100}% "
                f"操作资金:{cash} "
                f"交易对:{symbol} "
                )

    period = max(boll_period, rsi_period)
    cerebro = init_broker(ctx.obj, limit=period)
    cerebro.broker.setcash(cash)
    cerebro.addstrategy(
        Oscillation,
        boll_period=boll_period,
        boll_dev=boll_dev,
        rsi_period=rsi_period,
        rsi_buy_signal=rsi_buy_signal,
        stop_loss=stop_loss,
    )

    def signal_handler(signal, frame):
        logger.info("Signal received, stopping...")
        cerebro.runstop()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    cerebro.run()