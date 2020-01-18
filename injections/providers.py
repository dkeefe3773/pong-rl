import dependency_injector.containers as containers
import dependency_injector.providers as providers

from config import property_configurator
from gameengine.ball_to_ball_collision import BilliardBallCollider
from gameengine.ball_to_barrier_collision import IncidentAngleRebounder
from gameengine.ball_to_paddle_collision import update_white_ball, CollisionStrategyByColor, BallPaddleCollider
from gameengine.collision_engine import CollisionPairHandlerFactory, GameCollisionEngine
from gameserver.pong_server import PongServer
from gameserver.pong_servicer import DummyPongServicer
from paddles.do_nothing import DoNothingPaddle
from paddles.stationary import StationaryPaddle
from player.controller import PlayerController
from proto_gen.gamemaster_pb2 import PaddleType


class PaddleProviders(containers.DeclarativeContainer):
    """
    Container for paddle controllers
    """
    left_do_nothing_paddle = providers.Factory(DoNothingPaddle)
    right_do_nothing_paddle = providers.Factory(DoNothingPaddle)

    left_stationary_paddle = providers.Factory(StationaryPaddle)
    right_stationary_paddle = providers.Factory(StationaryPaddle)


class PlayerProviders(containers.DeclarativeContainer):
    """
    Container for player objects
    """
    left_player = providers.Singleton(PlayerController,
                                      name=property_configurator.player_config.left_player_name,
                                      paddle_type=PaddleType.LEFT,
                                      paddle_controller=PaddleProviders.left_stationary_paddle)

    right_player = providers.Singleton(PlayerController,
                                       name=property_configurator.player_config.right_player_name,
                                       paddle_type=PaddleType.RIGHT,
                                       paddle_controller=PaddleProviders.right_stationary_paddle)


class GameEngineProviders(containers.DeclarativeContainer):
    """
    Container for game engine objects
    """
    # ball to ball collisions
    ball_ball_collision_provider = providers.Singleton(BilliardBallCollider)

    # ball to barrier collisions
    ball_barrier_collision_provider = providers.Singleton(IncidentAngleRebounder)

    # ball to paddle collisions
    white_ball_paddle_collision_provider = providers.Callable(update_white_ball)
    collision_strategy_by_color_provider = providers.Singleton(CollisionStrategyByColor,
                                                      white_ball_callable_provider=white_ball_paddle_collision_provider.delegate())
    ball_paddle_collision_provider = providers.Singleton(BallPaddleCollider,
                                                         collision_strategy_by_color_provider)

    collision_pair_handler_factory_provider = providers.Singleton(CollisionPairHandlerFactory,
                                                                  ball_to_ball_handler = ball_ball_collision_provider,
                                                                  ball_to_barrier_handler = ball_barrier_collision_provider,
                                                                  ball_to_paddler_handler = ball_paddle_collision_provider)

    game_engine_provider = providers.Singleton(GameCollisionEngine,
                                               collision_pair_handler_factory = collision_pair_handler_factory_provider)



class ServicerProviders(containers.DeclarativeContainer):
    """
    Container for service providers
    """
    dummy_pong_servicer = providers.Factory(DummyPongServicer)


class GrpcServerProviders(containers.DeclarativeContainer):
    """
    Container for server providers
    """
    pong_server = providers.Singleton(PongServer,
                                      servicer=ServicerProviders.dummy_pong_servicer,
                                      max_workers=property_configurator.game_server_config.max_workers,
                                      thread_prefix=property_configurator.game_server_config.thread_pool_prefix,
                                      port=property_configurator.game_server_config.port)
