import random
from abc import ABC, abstractmethod
from typing import Optional

from shapely.geometry import Polygon

from config import logging_configurator
from proto_gen.gamemaster_pb2 import GameState, PaddleAction, PaddleDirective, PaddleType, Actor, ActorType

logger = logging_configurator.get_logger(__name__)


class PaddleController(ABC):
    def __init__(self, paddle_type: PaddleType):
        self._paddle_type = paddle_type

    @abstractmethod
    def process_game_state(self, game_state: GameState) -> Optional[PaddleAction]:
        """
        :param game_state: the state of the game
        :return: A paddle Action object or None for no action
        """
        pass

    @property
    def paddle_type(self) -> PaddleType:
        return self._paddle_type


class StationaryPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType):
        super().__init__(paddle_type)

    def process_game_state(self, game_state: GameState):
        logger.debug(f"Processing game state {game_state.state_iteration}")
        return PaddleAction(paddle_directive=PaddleDirective.STATIONARY)

class AlwaysUpPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType):
        super().__init__(paddle_type)

    def process_game_state(self, game_state: GameState):
        logger.debug(f"Processing game state {game_state.state_iteration}")
        return PaddleAction(paddle_directive=PaddleDirective.UP)

class AlwaysDownPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType):
        super().__init__(paddle_type)

    def process_game_state(self, game_state: GameState):
        logger.debug(f"Processing game state {game_state.state_iteration}")
        return PaddleAction(paddle_directive=PaddleDirective.DOWN)


class FollowTheBallPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType):
        super().__init__(paddle_type)

    def process_game_state(self, game_state: GameState):
        logger.debug(f"Processing game state {game_state.state_iteration}")
        primary_ball: Actor = next(
            filter(lambda actor: actor.actor_type is ActorType.PRIMARY_BALL, game_state.actors), None)

        if self.paddle_type is PaddleType.LEFT:
            my_paddle = next(filter(lambda actor: actor.actor_type is ActorType.LEFT_PADDLE, game_state.actors), None)
        else:
            my_paddle = next(filter(lambda actor: actor.actor_type is ActorType.RIGHT_PADDLE, game_state.actors), None)

        if primary_ball is None or my_paddle is None:
            logger.error("Primary ball or my paddle is not found in actor list")
            return PaddleAction(paddle_directive=PaddleDirective.STATIONARY)

        primary_ball_shape = Polygon([(coord.x, coord.y) for coord in primary_ball.coords])
        my_paddle_shape = Polygon([(coord.x, coord.y) for coord in my_paddle.coords])
        if primary_ball_shape.centroid.y < my_paddle_shape.centroid.y:
            directive = PaddleDirective.UP
        elif primary_ball_shape.centroid.y > my_paddle_shape.centroid.y:
            directive = PaddleDirective.DOWN
        else:
            # lets add some randomness here so that when the paddles play each other they don't get stuck in a loop
            directive = random.choice([PaddleDirective.UP, PaddleDirective.DOWN])
        return PaddleAction(paddle_directive=directive)
