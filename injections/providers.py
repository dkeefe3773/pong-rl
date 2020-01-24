from queue import Queue

import dependency_injector.containers as containers
import dependency_injector.providers as providers

from config import property_configurator
from gameengine.arena import Arena
from gameengine.ball_to_ball_collision import BilliardBallCollider
from gameengine.ball_to_barrier_collision import IncidentAngleRebounder
from gameengine.ball_to_paddle_collision import BallPaddleCollider, CollisionStrategyByFlavor, update_primary_ball
from gameengine.collision_engine import CollisionPairHandlerFactory, DefaultGameCollisionEngine
from gameengine.paddle_to_wall_collision import PaddleWallCollider
from gamerender.pongrenders import DefaultPongRenderer
from gameserver.pong_server import PongServer
from gameserver.pong_servicer import DummyPongServicer, DefaultPongServicer
from paddles.paddle import StationaryPaddle, FollowTheBallPaddle
from player.controller import PlayerController
from proto_gen.gamemaster_pb2 import PaddleType


class PaddleProviders(containers.DeclarativeContainer):
    """
    Container for paddle controllers
    """
    left_stationary_paddle = providers.Factory(StationaryPaddle, paddle_type = PaddleType.LEFT)
    right_stationary_paddle = providers.Factory(StationaryPaddle, paddle_type = PaddleType.RIGHT)

    left_follow_the_ball_paddle = providers.Factory(FollowTheBallPaddle, paddle_type = PaddleType.LEFT)
    right_follow_the_ball_paddle = providers.Factory(FollowTheBallPaddle, paddle_type = PaddleType.RIGHT)


class PlayerProviders(containers.DeclarativeContainer):
    """
    Container for player objects
    """
    left_player = providers.Singleton(PlayerController,
                                      name=property_configurator.player_config.left_player_name,
                                      paddle_type=PaddleType.LEFT,
                                      paddle_controller=PaddleProviders.left_follow_the_ball_paddle)

    right_player = providers.Singleton(PlayerController,
                                       name=property_configurator.player_config.right_player_name,
                                       paddle_type=PaddleType.RIGHT,
                                       paddle_controller=PaddleProviders.right_follow_the_ball_paddle)


class GameArenaProvider(containers.DeclarativeContainer):
    default_arena = providers.Singleton(Arena)


class GameEngineProviders(containers.DeclarativeContainer):
    """
    Container for game engine objects
    """
    # ball to ball collisions
    ball_ball_collision = providers.Singleton(BilliardBallCollider)

    # ball to barrier collisions
    ball_barrier_collision = providers.Singleton(IncidentAngleRebounder)

    # ball to paddle collisions
    primary_ball_paddle_collision = providers.Callable(update_primary_ball)
    collision_strategy_by_flavor = providers.Singleton(CollisionStrategyByFlavor,
                                                       primary_ball_callable_provider=primary_ball_paddle_collision.delegate())
    ball_paddle_collision = providers.Singleton(BallPaddleCollider,
                                                classic_paddle_collision_factory=collision_strategy_by_flavor)

    paddle_wall_collision = providers.Singleton(PaddleWallCollider)

    collision_pair_handler_factory = providers.Singleton(CollisionPairHandlerFactory,
                                                         ball_to_ball_handler=ball_ball_collision,
                                                         ball_to_barrier_handler=ball_barrier_collision,
                                                         ball_to_paddle_handler=ball_paddle_collision,
                                                         paddle_to_wall_handler=paddle_wall_collision)

    game_engine = providers.Singleton(DefaultGameCollisionEngine,
                                      collision_pair_handler_factory=collision_pair_handler_factory)


class ThreadCommunicationProviders(containers.DeclarativeContainer):
    """
    Container for thread safe communication objects
    """
    left_game_state_queue = providers.Singleton(Queue)
    right_game_state_queue = providers.Singleton(Queue)
    left_paddle_action_queue = providers.Singleton(Queue)
    right_paddle_action_queue = providers.Singleton(Queue)


class GameRendererProviders(containers.DeclarativeContainer):
    """
    Container for game rendering objects
    """
    pong_renderer = providers.Factory(DefaultPongRenderer,
                                      arena=GameArenaProvider.default_arena,
                                      game_engine=GameEngineProviders.game_engine,
                                      left_paddle_queue=ThreadCommunicationProviders.left_paddle_action_queue,
                                      right_paddle_queue=ThreadCommunicationProviders.right_paddle_action_queue,
                                      left_game_state_queue=ThreadCommunicationProviders.left_game_state_queue,
                                      right_game_state_queue=ThreadCommunicationProviders.right_game_state_queue,
                                      )


class ServicerProviders(containers.DeclarativeContainer):
    """
    Container for service providers
    """
    # For testing
    dummy_pong_servicer = providers.Factory(DummyPongServicer)

    # the real deal
    default_pong_servicer = \
        providers.Factory(DefaultPongServicer,
                          left_paddle_queue=ThreadCommunicationProviders.left_paddle_action_queue,
                          right_paddle_queue=ThreadCommunicationProviders.right_paddle_action_queue,
                          left_game_state_queue=ThreadCommunicationProviders.left_game_state_queue,
                          right_game_state_queue=ThreadCommunicationProviders.right_game_state_queue,
                          pong_renderer=GameRendererProviders.pong_renderer)

class GrpcServerProviders(containers.DeclarativeContainer):
    """
    Container for server providers
    """
    pong_server = providers.Singleton(PongServer,
                                      servicer=ServicerProviders.default_pong_servicer,
                                      max_workers=property_configurator.game_server_config.max_workers,
                                      thread_prefix=property_configurator.game_server_config.thread_pool_prefix,
                                      port=property_configurator.game_server_config.port)
