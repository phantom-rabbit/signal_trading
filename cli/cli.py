import os.path

import click
from .candles import candles
from .live_trading import live_trading
from .back_strategy import back_strategy
from loguru import logger
import toml

@click.group()
@click.option('--config', type=click.File('r'), help='Path to the configuration file.')
@click.pass_context
def cli(ctx, config):
    if config:
        ctx.obj = toml.load(config)
        logger.add(os.path.join(ctx.obj['workdir'], "signal_trading.log"), level="DEBUG", format="{time} {level} {message}")
    else:
        ctx.obj = {}
    pass


cli.add_command(candles, "candles")
cli.add_command(live_trading, "live_trading")
cli.add_command(back_strategy, "back-strategy")

