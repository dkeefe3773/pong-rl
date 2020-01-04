import click

from config import logging_configurator
from gameserver.pong_server import PongServer
from injections.providers import GrpcServerProviders

logger = logging_configurator.get_logger(__name__)


@click.command()
def cli():
    """
    This will start the grpc server for the pong service.  The listen port is configurable within the config.ini.
    The server will run until this process is killed.
    """
    logger.info("Starting the Pong Game Master GRPC Server")
    pong_server: PongServer = GrpcServerProviders.pong_server()
    pong_server.start_server_blocking()


if __name__ == '__main__':
    cli()
