import os.path

import click
from .candles import candles
from .live_trading import live_trading
from loguru import logger

@click.group()
@click.option('--work_dir', default='/data/', help='Path to the dir.')
@click.pass_context
def cli(ctx, work_dir):
    ctx.ensure_object(dict)
    ctx.obj['work_dir'] = work_dir
    logger.add(os.path.join(work_dir, "signal_trading.log"), level="DEBUG", format="{time} {level} {message}")
    pass


cli.add_command(candles, "candles")
cli.add_command(live_trading, "live_trading")
