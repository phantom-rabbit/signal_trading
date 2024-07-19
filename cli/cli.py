import click
from .candles import candles
from .live_trading import live_trading


@click.group()
def cli():
    pass


cli.add_command(candles, "candles")
cli.add_command(live_trading, "live_trading")
