import random
from abc import ABC, abstractmethod
from typing import Optional

from config import logging_configurator
from paddles.paddle_utils import GameStateWrapper
from proto_gen.gamemaster_pb2 import PaddleAction, PaddleDirective, PaddleType, GameStateBuffer

logger = logging_configurator.get_logger(__name__)


class PaddleController(ABC):
    def __init__(self, paddle_type: PaddleType, mirror_image: bool = False, preserve_alpha: bool = False):
        """

        :param paddle_type:    left of right
        :param mirror_image:   if true, then the game_state_wrapper will provide actor objects and the image array
        itself in coordinates that have been mirrored across the center column of the arena.  In other words,
        left becomes right and right becomes left.  This is useful if a paddle model has been trained on the
        left hand side so that it can be used on the right hand side
        :param preserve_alpha: if true, the alpha channel will be preserved in the grey scale and rgb images
        """
        self._paddle_type = paddle_type
        self.game_state_wrapper = GameStateWrapper(paddle_type, mirror_image, preserve_alpha)

    @abstractmethod
    def process_game_state(self, game_state_buffer: GameStateBuffer) -> Optional[PaddleAction]:
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

    def process_game_state(self, game_state_buffer: GameStateBuffer):
        return PaddleAction(paddle_directive=PaddleDirective.STATIONARY)


class AlwaysUpPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType):
        super().__init__(paddle_type)

    def process_game_state(self, game_state_buffer: GameStateBuffer):
        return PaddleAction(paddle_directive=PaddleDirective.UP)


class AlwaysDownPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType):
        super().__init__(paddle_type)

    def process_game_state(self, game_state_buffer: GameStateBuffer):
        return PaddleAction(paddle_directive=PaddleDirective.DOWN)


class FollowTheBallPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType):
        super().__init__(paddle_type)

    def process_game_state(self, game_state_buffer: GameStateBuffer):
        # lets just get the most recent game state
        self.game_state_wrapper.game_state = game_state_buffer.game_states[-1]
        primary_ball = self.game_state_wrapper.primary_ball
        my_paddle = self.game_state_wrapper.my_paddle

        if primary_ball.shape.centroid.y < my_paddle.shape.centroid.y:
            directive = PaddleDirective.UP
        elif primary_ball.shape.centroid.y > my_paddle.shape.centroid.y:
            directive = PaddleDirective.DOWN
        else:
            # lets add some randomness here so that when the paddles play each other they don't get stuck in a loop
            directive = random.choice([PaddleDirective.UP, PaddleDirective.DOWN])
        return PaddleAction(paddle_directive=directive)


class EnhancedFollowTheBallPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType, mirror_image=False):
        super().__init__(paddle_type, mirror_image)

    def process_game_state(self, game_state_buffer: GameStateBuffer):
        # lets just get the most recent game state
        self.game_state_wrapper.game_state = game_state_buffer.game_states[-1]
        primary_ball = self.game_state_wrapper.primary_ball
        my_paddle = self.game_state_wrapper.my_paddle

        ball_moving_away = primary_ball.vel.vel_x > 0
        if ball_moving_away:
            arena_height = self.game_state_wrapper.image_grey_array.shape[0] // 2
            if my_paddle.shape.centroid.y > arena_height:
                directive = PaddleDirective.UP
            elif my_paddle.shape.centroid.y < arena_height:
                directive = PaddleDirective.DOWN
            else:
                directive = PaddleDirective.STATIONARY
        else:
            if primary_ball.shape.centroid.y < my_paddle.shape.centroid.y:
                directive = PaddleDirective.UP
            elif primary_ball.shape.centroid.y > my_paddle.shape.centroid.y:
                directive = PaddleDirective.DOWN
            else:
                # lets add some randomness here so that when the paddles play each other they don't get stuck in a loop
                directive = random.choice([PaddleDirective.UP, PaddleDirective.DOWN])
        return PaddleAction(paddle_directive=directive)
