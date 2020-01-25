import contextlib
from typing import Generator

import grpc

from config import logging_configurator
from proto_gen.gamemaster_pb2 import GameState, PlayerIdentifier, PaddleAction, GameStateBuffer

logger = logging_configurator.get_logger(__name__)

from proto_gen.gamemaster_pb2_grpc import GameMasterStub
from config.property_configurator import GameServerConfig

_game_server_config = GameServerConfig()
_game_master_address = "{}:{}".format(_game_server_config.host, _game_server_config.port)

_global_channel = grpc.insecure_channel(_game_master_address)
_global_stub = GameMasterStub(_global_channel)


@contextlib.contextmanager
def get_transactional_server_stub() -> Generator[GameMasterStub, None, None]:
    """
    A generator wrapped in a context manager to provide a transactional stub.  When the context manager
    exit is invoked, the stub will go out of scope, which in turn closes the channel.
    :return: a generator that yields a GameMasterStub
    """
    with grpc.insecure_channel(_game_master_address) as channel:
        server_stub = GameMasterStub(channel)
        yield server_stub
        logger.info("Transactional GameMasterStub going out of scope")
    logger.info("Transactional channel to GameMasterService is now closed")


def register_player(player_identifier: PlayerIdentifier):
    """
    Game service is notified that the player is ready to play!
    :param player_identifier: identity object for player
    :return:  None
    """
    with get_transactional_server_stub() as game_master_stub:
        game_master_stub.register_player(player_identifier)
        logger.info("Player {}:{} has registered with the game server".format(player_identifier.player_name,
                                                                              player_identifier.paddle_strategy_name));


def serve_game_states(playerIdentifier: PlayerIdentifier) -> Generator[GameStateBuffer, None, None]:
    """
    A generator for game state
    :return: an iterator over game states
    """
    with get_transactional_server_stub() as game_master_stub:
        game_state_iterator = game_master_stub.stream_game_state(playerIdentifier)
        for game_state_buffer in game_state_iterator:
            yield game_state_buffer


def submit_paddle_action_iterator(paddle_action_iterator: Generator[PaddleAction, None, None]):
    """
    This will make an asynchronous call to the server api submit_paddle_actions, which is expected to be a
    generator
    :param paddle_action: a generator for paddle actions
    :return: None
    """
    # need to use global channel here because server will be using the tcp connection (the channel) to callback
    # into the generator so we need channel to stay alive
    call_future = _global_stub.submit_paddle_actions.future(paddle_action_iterator)
    call_future.add_done_callback(
        lambda response: logger.info("Client has submitted the paddle action generator to server"))


def close_global_channel():
    """
    Will terminate the global channel to the server.  In most cases, from my testing, if a client is terminated,
    the channel will be closed.  However, if the server is keeping the channel alive (because of a request stream generator)
    then the server will have a hung service thread.  So, moral of story: clients should call into this close method
    before termination
    :return: None
    """
    logger.info("Closing global channel")
    _global_channel.close()
