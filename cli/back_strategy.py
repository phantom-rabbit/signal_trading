import os.path

import click
from loguru import logger
import pandas as pd
import backtrader as bt
from analyzer import PositionReturn
from strategy import EMA_Crossover, EMA, SMA, Busy
from .utils import result_handler, COMMA_SEPARATED_LIST, COMMA_SEPARATED_LIST_INT
from pathlib import Path

def create_cerebro(filepath, cash, maxcpus):
    try:
        df = pd.read_csv(filepath, index_col='timestamp', parse_dates=True)
    except Exception as e:
        logger.error("f 数据读取出错:{df}")
        raise e

    if df.empty:
        return

    data = bt.feeds.PandasData(dataname=df)
    cerebro = bt.Cerebro(runonce=True, preload=True, optreturn=False, maxcpus=maxcpus)
    cerebro.adddata(data)
    cerebro.broker.setcash(cash)
    return cerebro

@click.group()
@click.pass_context
@click.option('--cash', default=10000, help='初始投入资金')
@click.option('--debug', default=True)
@click.option('--f', '--file', 'filepath', required=True, help="数据文件 csv")
@click.option('-o', '--output', 'output_dir', help="输出目录")
@click.option('--maxcpus', default=os.cpu_count())
@click.option('--opt', default=False, is_flag=True, help="参数寻优, 结果输出表格")
def back_strategy(ctx, cash, debug, filepath, output_dir, maxcpus, opt):
    """策略回测"""
    ctx.obj = {'cash': cash, 'debug': debug, 'filepath': filepath, 'output_dir': output_dir, 'maxcpus': maxcpus,
               'opt': opt}

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    logger.info(
        f"params cash:{cash} filepath:{filepath} output_dir:{output_dir} cpus:{maxcpus} opt:{opt} debug:{debug}")

@back_strategy.command()
@click.pass_context
@click.option('--short_period', type=COMMA_SEPARATED_LIST_INT, required=True, help="短周期")
@click.option('--long_period', type=COMMA_SEPARATED_LIST_INT, required=True, help="长周期")
@click.option('--below', type=COMMA_SEPARATED_LIST, required=True, help="低于周期的百分比买入")
@click.option("--net_profit", type=COMMA_SEPARATED_LIST, required=True, help="固定收益百分比")
@click.option("--stop_loss", type=COMMA_SEPARATED_LIST, required=True, help="风险控制百分比")
def sma_busy(ctx, short_period, long_period, below, net_profit, stop_loss):
    """
    策略 [ema指数交叉]
    黄金交叉买入，死亡交叉卖出
    """
    cash = ctx.obj['cash']
    filepath = ctx.obj['filepath']
    output_dir = ctx.obj['output_dir']
    maxcpus = ctx.obj['maxcpus']
    opt = ctx.obj['opt']

    logger.info(f"short_period:{short_period}")
    logger.info(f"long_period:{long_period}")
    logger.info(f"below:{below}")
    logger.info(f"net_profit:{net_profit}")
    logger.info(f"stop_loss:{stop_loss}")
    logger.info(f"maxcpus:{maxcpus}")

    cerebro = create_cerebro(filepath, cash, maxcpus)
    cerebro.optstrategy(
        Busy,
        short_period=short_period,
        long_period=long_period,
        below=below,
        net_profit=net_profit,
        stop_loss=stop_loss,
    )
    # 运行策略
    results = cerebro.run()
    data_source = Path(filepath).stem
    filename = f"{data_source}_ema_busy"
    if output_dir:
        filename = os.path.join(output_dir, filename)
    result_handler(results, filename, opt)

