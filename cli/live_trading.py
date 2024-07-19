import datetime
import os.path

import backtrader as bt
import click
from analyzer import PositionReturn, OKXLiveTradeAnalyzer
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.TradeModel import Base
from broker import OKXData, OKXBroker
from strategy import SMA, EMA, EMA_Crossover
import signal


@click.group()
@click.pass_context
def live_trading(ctx):
    """实盘交易"""
    workdir = ctx.obj['workdir']
    directory = os.path.join(workdir, "database")
    os.makedirs(directory, exist_ok=True)
    ctx.obj['database'] = directory


@live_trading.command()
@click.pass_context
@click.option('--symbol', default='BTC/USDT', help='交易对')
@click.option('--interval', default='1m', help='交易间隔，查看okx candles参数')
@click.option('--cash', default=100, help='初始投入资金')
@click.option('--debug', default=True)
@click.option('--period', default=3, help="周期")
@click.option('--below', default=0.05, help="低于周期的百分比买入 默认百分之5")
@click.option('--above', default=0.05, help="高于周期的百分比卖出 默认百分之5")
def sma(ctx, symbol, cash, interval, period, below, above, debug=True):
    """
    策略 [简单移动均线指标]
        均线周期的平均价以下买入,在均线周期的平均价以上卖出
    """

    api_key = ctx.obj['API']['api_key']
    secret = ctx.obj['API']['secret']
    password = ctx.obj['API']['password']
    is_testnet = ctx.obj['API']['is_testnet']

    data = OKXData(symbol=symbol, interval=interval, online_data=True, is_testnet=is_testnet, debug=debug)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcash(cash)

    DATABASE_URL = f'sqlite://{ctx.obj["database"]}/database/trade_records.db'
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    Base.metadata.create_all(bind=engine)
    cerebro.addanalyzer(OKXLiveTradeAnalyzer, db=session)

    broker = OKXBroker(
        api_key=api_key,
        secret=secret,
        password=password,
        symbol=symbol,
        cash=cash,
        is_testnet=is_testnet,
        debug=debug,
    )
    cerebro.setbroker(broker)

    cerebro.addstrategy(SMA, period=period, below=below, above=above, debug=debug)
    # 注册信号处理函数
    def signal_handler(signal, frame):
        logger.info("Signal received, stopping...")
        data.stop()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行策略
    cerebro.run()
    # result_handler(run, f"{datetime.datetime.now()}_SMA")

@live_trading.command()
@click.option('--symbol', default='BTC/USDT', help='交易对')
@click.option('--interval', default='1m', help='交易间隔，查看okx candles参数')
@click.option('--cash', default=100, help='初始投入资金')
@click.option('--debug', default=True)
@click.option('--period', default=3, help="周期")
@click.option('--below', default=0.05, help="低于周期的百分比买入 默认百分之5")
@click.option('--above', default=0.05, help="高于周期的百分比卖出 默认百分之5")
@click.pass_context
def ema(ctx, symbol, cash, interval, period, below, above, debug=True):
    """
    策略 [指数平均数指标]
        均线周期的平均价以下买入,在均线周期的平均价以上卖出
    """

    api_key = ctx.obj['API']['api_key']
    secret = ctx.obj['API']['secret']
    password = ctx.obj['API']['password']
    is_testnet = ctx.obj['API']['is_testnet']

    data = OKXData(symbol=symbol, interval=interval, online_data=True, is_testnet=is_testnet, debug=debug)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcash(cash)

    DATABASE_URL = f'sqlite://{ctx.obj["database"]}/database/trade_records.db'
    print(DATABASE_URL)
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    Base.metadata.create_all(bind=engine)
    cerebro.addanalyzer(OKXLiveTradeAnalyzer, db=session)

    broker = OKXBroker(
        api_key=api_key,
        secret=secret,
        password=password,
        symbol=symbol,
        cash=cash,
        is_testnet=is_testnet,
        debug=debug,
    )
    cerebro.setbroker(broker)

    cerebro.addstrategy(EMA, period=period, below=below, above=above, debug=debug)
    # 注册信号处理函数
    def signal_handler(signal, frame):
        logger.info("Signal received, stopping...")
        data.stop()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行策略
    cerebro.run()
    # result_handler(run, f"{datetime.datetime.now()}_SMA")

@live_trading.command()
@click.pass_context
@click.option('--symbol', default='BTC/USDT', help='交易对')
@click.option('--interval', default='1m', help='交易间隔，查看okx candles参数')
@click.option('--cash', default=100, help='初始投入资金')
@click.option('--debug', default=True)
@click.option('--short_period', default=20, help="短周期")
@click.option('--long_period', default=120, help="长周期")
def ema_crossover(ctx, symbol, cash, interval, short_period, long_period, debug=True):
    """
    策略 [ema指数交叉]
    黄金交叉买入，死亡交叉卖出
    """

    api_key = ctx.obj['API']['api_key']
    secret = ctx.obj['API']['secret']
    password = ctx.obj['API']['password']
    is_testnet = ctx.obj['API']['is_testnet']

    data = OKXData(symbol=symbol, interval=interval, online_data=True, is_testnet=is_testnet, debug=debug)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcash(cash)

    DATABASE_URL = f'sqlite://{ctx.obj["database"]}/database/trade_records.db'
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    Base.metadata.create_all(bind=engine)
    cerebro.addanalyzer(OKXLiveTradeAnalyzer, db=session)

    broker = OKXBroker(
        api_key=api_key,
        secret=secret,
        password=password,
        symbol=symbol,
        cash=cash,
        is_testnet=is_testnet,
        debug=debug,
    )
    cerebro.setbroker(broker)

    cerebro.addstrategy(EMA_Crossover, short_period=short_period, long_period=long_period, debug=debug)
    # 注册信号处理函数
    def signal_handler(signal, frame):
        logger.info("Signal received, stopping...")
        data.stop()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行策略
    cerebro.run()
