import os.path
import sys

import click
from .candles import candles
from .live_trading import live_trading
from .back_strategy import back_strategy


@click.group()
def cli():
    pass


cli.add_command(candles, "candles")
cli.add_command(live_trading, "live")
cli.add_command(back_strategy, "backtest")

