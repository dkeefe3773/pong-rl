import dependency_injector.containers as containers
import dependency_injector.providers as providers

from config import property_configurator
from gameserver.pong_server import PongServer
from gameserver.pong_servicer import DummyPongServicer
from paddles.do_nothing import DoNothingPaddle
from paddles.stationary import StationaryPaddle
from player.controller import PlayerController
from proto_gen.gamemaster_pb2 import PaddleType


class PaddleProviders(containers.DeclarativeContainer):
    """
    Factory provider for paddle controllers
    """
    left_do_nothing_paddle = providers.Factory(DoNothingPaddle)
    right_do_nothing_paddle = providers.Factory(DoNothingPaddle)

    left_stationary_paddle = providers.Factory(StationaryPaddle)
    right_stationary_paddle = providers.Factory(StationaryPaddle)


class PlayerProviders(containers.DeclarativeContainer):
    """
    Factory provider for players
    """
    left_player = providers.Singleton(PlayerController,
                                      name=property_configurator.player_config.left_player_name,
                                      paddle_type=PaddleType.LEFT,
                                      paddle_controller=PaddleProviders.left_stationary_paddle)

    right_player = providers.Singleton(PlayerController,
                                       name=property_configurator.player_config.right_player_name,
                                       paddle_type=PaddleType.RIGHT,
                                       paddle_controller=PaddleProviders.right_stationary_paddle)


class ServicerProviders(containers.DeclarativeContainer):
    """
    Factory provider for service implementations
    """
    dummy_pong_servicer = providers.Factory(DummyPongServicer)


class GrpcServerProviders(containers.DeclarativeContainer):
    """
    Factory provider for servers
    """
    pong_server = providers.Singleton(PongServer,
                                      servicer=ServicerProviders.dummy_pong_servicer,
                                      max_workers=property_configurator.game_server_config.max_workers,
                                      thread_prefix=property_configurator.game_server_config.thread_pool_prefix,
                                      port=property_configurator.game_server_config.port)
